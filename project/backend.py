from __future__ import annotations
import os
import sys
import io
import json
import uuid
import base64
import sqlite3
import tempfile
import smtplib
import requests
import qrcode
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from PIL import Image
from datetime import datetime, timezone, timedelta
import threading
from dotenv import load_dotenv
from pydub import AudioSegment
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

# bank/ 폴더의 LocalEmbeddings 재사용
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bank"))
from embeddings import LocalEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import AzureChatOpenAI

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
AudioSegment.converter = "/Users/kimminyoung/opt/anaconda3/bin/ffmpeg"

# ── RAG: 과거 편지 벡터 DB ──────────────────────────────────
DIARY_CHROMA_DIR = os.path.join(os.path.dirname(__file__), "diary_chroma_db")
_vectorstore = None

def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            persist_directory=DIARY_CHROMA_DIR,
            embedding_function=LocalEmbeddings(),
        )
    return _vectorstore

def search_past_letters(text: str, k: int = 3) -> list[str]:
    try:
        docs = get_vectorstore().similarity_search(text, k=k)
        return [doc.page_content for doc in docs]
    except Exception:
        return []

def save_letter_to_vectorstore(stt_text: str, letter: str, emotions: list, keywords: list, kakao_id: str = "anonymous"):
    date_str = datetime.now().strftime("%Y년 %m월 %d일")
    content = (
        f"날짜: {date_str}\n"
        f"감정: {', '.join(emotions)}\n"
        f"키워드: {', '.join(keywords)}\n"
        f"오늘의 기록: {stt_text}\n"
        f"편지:\n{letter}"
    )
    get_vectorstore().add_documents([
        Document(page_content=content, metadata={"date": date_str, "kakao_id": kakao_id})
    ])


KAKAO_KEY     = os.getenv("KAKAO_REST_API_KEY")
KAKAO_SECRET  = os.getenv("KAKAO_CLIENT_SECRET")
REDIRECT_URI  = "http://localhost:5173/kakao/callback"
DB_PATH       = os.path.join(os.path.dirname(__file__), "schedules.db")

# 카카오 OAuth 상태 임시 저장 (메모리) — kakao_id, nickname 포함
oauth_states: dict = {}

# ── DB 초기화 ───────────────────────────────────────────────
FRONTEND_URL = "http://192.168.200.181:5173"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            kakao_id   TEXT PRIMARY KEY,
            nickname   TEXT,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id         TEXT PRIMARY KEY,
            kakao_id   TEXT,
            letter     TEXT,
            emotions   TEXT,
            keywords   TEXT,
            date       TEXT,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id              TEXT PRIMARY KEY,
            kakao_id        TEXT,
            letter          TEXT,
            emotions        TEXT,
            keywords        TEXT,
            date_created    TEXT,
            date_scheduled  TEXT,
            refresh_token   TEXT,
            status          TEXT DEFAULT 'pending',
            send_method     TEXT DEFAULT 'kakao',
            discord_webhook TEXT,
            target_email    TEXT
        )
    """)
    for col, typ in [
        ("send_method",     "TEXT DEFAULT 'kakao'"),
        ("discord_webhook", "TEXT"),
        ("target_email",    "TEXT"),
        ("kakao_id",        "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE schedules ADD COLUMN {col} {typ}")
        except sqlite3.OperationalError:
            pass
    for col, typ in [("kakao_id", "TEXT")]:
        try:
            conn.execute(f"ALTER TABLE cards ADD COLUMN {col} {typ}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


# ── 카카오 유저 프로필 조회 ──────────────────────────────────
def fetch_kakao_profile(access_token: str) -> dict:
    resp = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if resp.status_code != 200:
        return {}
    data = resp.json()
    kakao_id = str(data.get("id", ""))
    nickname = data.get("kakao_account", {}).get("profile", {}).get("nickname", "")
    return {"kakao_id": kakao_id, "nickname": nickname}


def upsert_user(kakao_id: str, nickname: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO users (kakao_id, nickname, created_at) VALUES (?,?,?) "
        "ON CONFLICT(kakao_id) DO UPDATE SET nickname=excluded.nickname",
        (kakao_id, nickname, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()

init_db()

# ── 카카오 메시지 발송 (스케줄러 호출) ──────────────────────
def send_kakao_message(job_id: str):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT letter, emotions, refresh_token, status FROM schedules WHERE id=?", (job_id,)
    ).fetchone()
    if not row or row[3] != "pending":
        conn.close()
        return

    letter, emotions_json, refresh_token, _ = row

    # 액세스 토큰 갱신
    resp = requests.post("https://kauth.kakao.com/oauth/token", data={
        "grant_type":    "refresh_token",
        "client_id":     KAKAO_KEY,
        "client_secret": KAKAO_SECRET,
        "refresh_token": refresh_token,
    })
    if resp.status_code != 200:
        conn.execute("UPDATE schedules SET status='failed' WHERE id=?", (job_id,))
        conn.commit(); conn.close()
        print(f"[Kakao] 토큰 갱신 실패: {resp.text}")
        return

    token_data    = resp.json()
    access_token  = token_data["access_token"]
    new_refresh   = token_data.get("refresh_token", refresh_token)
    if new_refresh != refresh_token:
        conn.execute("UPDATE schedules SET refresh_token=? WHERE id=?", (new_refresh, job_id))

    # 메시지 전송
    emotions = json.loads(emotions_json)
    preview  = letter[:120] + "..." if len(letter) > 120 else letter
    template = {
        "object_type": "text",
        "text": f"💌 미래의 나에게\n\n{preview}\n\n{' '.join(emotions)}",
        "link": {"web_url": "http://localhost:5173", "mobile_web_url": "http://localhost:5173"},
        "button_title": "편지 전체 보기",
    }

    send_resp = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
    )

    status = "sent" if send_resp.status_code == 200 else "failed"
    conn.execute("UPDATE schedules SET status=? WHERE id=?", (status, job_id))
    conn.commit(); conn.close()
    print(f"[Kakao] 발송 {status}: {job_id}")


# ── Discord 웹훅 발송 ────────────────────────────────────────
def send_discord_message(job_id: str, webhook_url: str, letter: str, emotions: list, keywords: list):
    preview = letter[:400] + "..." if len(letter) > 400 else letter
    payload = {
        "embeds": [{
            "title": "💌 미래의 나에게 | Dear Me,",
            "description": preview,
            "color": 0xC4985A,
            "fields": [
                {"name": "오늘의 감정", "value": " ".join(emotions), "inline": True},
                {"name": "키워드", "value": "  ".join(f"#{k}" for k in keywords), "inline": True},
            ],
            "footer": {"text": f"📅 {datetime.now().strftime('%Y년 %m월 %d일')} | Time Capsule Letter"},
        }]
    }
    conn = sqlite3.connect(DB_PATH)
    try:
        resp = requests.post(webhook_url, json=payload)
        status = "sent" if resp.status_code in (200, 204) else "failed"
        print(f"[Discord] 발송 {status}: {job_id} ({resp.status_code})")
    except Exception as e:
        status = "failed"
        print(f"[Discord] 발송 오류: {e}")
    conn.execute("UPDATE schedules SET status=? WHERE id=?", (status, job_id))
    conn.commit(); conn.close()


# ── 이메일 발송 ──────────────────────────────────────────────
def send_email_message(job_id: str, to_email: str, letter: str, emotions: list, keywords: list):
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_pass:
        print("[Email] .env에 SMTP_USER, SMTP_PASSWORD가 없습니다.")
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE schedules SET status='failed' WHERE id=?", (job_id,))
        conn.commit(); conn.close()
        return

    # QR 코드 생성
    qr_bytes = None
    try:
        qr = qrcode.QRCode(version=1, box_size=8, border=3)
        qr.add_data(letter)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#3D2B1F", back_color="white").convert("RGB")
        buf = io.BytesIO()
        qr_img.save(buf, format="PNG")
        qr_bytes = buf.getvalue()
    except Exception as e:
        print(f"[Email] QR 생성 오류: {e}")

    letter_html   = "".join(
        f'<p style="margin:0 0 {"14px" if line == "" else "2px"};min-height:{"14px" if line == "" else "auto"};">{line if line else "&nbsp;"}</p>'
        for line in letter.split("\n")
    )
    emotion_tags  = "".join(
        f'<span style="display:inline-block;background:rgba(196,152,90,0.12);border:1px solid #E8D5B0;border-radius:20px;padding:5px 14px;font-size:14px;color:#2C1A0E;margin:3px;font-family:Georgia,serif;">{e}</span>'
        for e in emotions
    )
    keyword_tags  = "&nbsp;&nbsp;".join(
        f'<span style="font-size:12px;color:#C4985A;letter-spacing:0.5px;">#{k}</span>'
        for k in keywords
    )
    qr_tag        = '<img src="cid:qrcode" width="80" height="80" style="width:80px;height:80px;border-radius:8px;border:1px solid #E8D5B0;display:block;" />' if qr_bytes else ''
    date_str      = datetime.now().strftime("%Y년 %m월 %d일")

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300;400&family=Noto+Sans+KR:wght@400;500&display=swap" rel="stylesheet">
</head>
<body style="margin:0;padding:24px;background:#f0e0cc;font-family:'Noto Serif KR',Georgia,serif;">
<div style="max-width:560px;margin:0 auto;background:linear-gradient(160deg,#FDF6EC 0%,#F5E8D0 100%);border-radius:20px;padding:48px 44px 40px;border:1px solid #E8D5B0;position:relative;">

  <!-- 안쪽 테두리 -->
  <table style="position:absolute;top:8px;left:8px;right:8px;bottom:8px;width:calc(100% - 16px);border-collapse:collapse;pointer-events:none;">
    <tr><td style="border:1px solid #E8D5B0;border-radius:14px;"></td></tr>
  </table>

  <!-- 상단 장식 -->
  <table style="width:100%;border-collapse:collapse;margin-bottom:32px;">
    <tr>
      <td style="border-bottom:1px solid #E8D5B0;width:40%;"></td>
      <td style="white-space:nowrap;padding:0 10px;font-size:10px;letter-spacing:3px;color:#C4985A;font-family:'Noto Sans KR',Arial,sans-serif;text-align:center;">✦ TIME CAPSULE ✦</td>
      <td style="border-bottom:1px solid #E8D5B0;width:40%;"></td>
    </tr>
  </table>

  <!-- 제목 영역 -->
  <div style="text-align:center;margin-bottom:24px;">
    <div style="font-size:40px;line-height:1;margin-bottom:8px;">💌</div>
    <h1 style="font-family:'Noto Serif KR',Georgia,serif;font-size:42px;font-weight:300;color:#2C1A0E;margin:0 0 8px;letter-spacing:-0.5px;">Dear Me</h1>
    <p style="font-size:12px;color:#7A5C3A;letter-spacing:1px;margin:0;font-family:'Noto Sans KR',Arial,sans-serif;">{date_str}</p>
  </div>

  <!-- 감정 태그 -->
  <div style="text-align:center;margin-bottom:10px;">{emotion_tags}</div>

  <!-- 키워드 -->
  <div style="text-align:center;margin-bottom:28px;">{keyword_tags}</div>

  <!-- 구분선 -->
  <table style="width:100%;border-collapse:collapse;margin-bottom:28px;">
    <tr>
      <td style="border-bottom:1px solid #E8D5B0;"></td>
      <td style="white-space:nowrap;padding:0 10px;font-size:10px;color:#C4985A;">✦</td>
      <td style="border-bottom:1px solid #E8D5B0;"></td>
    </tr>
  </table>

  <!-- 편지 본문 -->
  <div style="font-size:14px;line-height:2.1;color:#3a2510;background:rgba(255,255,255,0.5);border-radius:12px;padding:20px 24px;margin-bottom:32px;border:1px solid rgba(232,213,176,0.6);">
    {letter_html}
  </div>

  <!-- 하단: 장식 + QR -->
  <table style="width:100%;border-collapse:collapse;">
    <tr>
      <td style="vertical-align:bottom;font-size:10px;color:#C4985A;letter-spacing:2px;font-family:'Noto Sans KR',Arial,sans-serif;">✦ Time Capsule Letter ✦</td>
      <td style="vertical-align:bottom;text-align:right;width:96px;">
        {qr_tag}
        <p style="font-size:9px;color:#7A5C3A;margin:4px 0 0;text-align:center;letter-spacing:0.5px;font-family:'Noto Sans KR',Arial,sans-serif;">편지 보기</p>
      </td>
    </tr>
  </table>

</div>
</body>
</html>"""

    # multipart/related: HTML + 인라인 이미지
    msg = MIMEMultipart("related")
    msg["Subject"] = "💌 미래의 나에게 - Dear Me"
    msg["From"]    = smtp_user
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html", "utf-8"))

    if qr_bytes:
        img_part = MIMEImage(qr_bytes, _subtype="png")
        img_part.add_header("Content-ID", "<qrcode>")
        img_part.add_header("Content-Disposition", "inline", filename="qr.png")
        msg.attach(img_part)

    conn = sqlite3.connect(DB_PATH)
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
        status = "sent"
        print(f"[Email] 발송 완료: {to_email}")
    except Exception as e:
        status = "failed"
        print(f"[Email] 발송 실패: {e}")
    conn.execute("UPDATE schedules SET status=? WHERE id=?", (status, job_id))
    conn.commit(); conn.close()


# ── 발송 채널 dispatcher ─────────────────────────────────────
def dispatch_message(job_id: str):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT letter, emotions, keywords, refresh_token, status, send_method, discord_webhook, target_email"
        " FROM schedules WHERE id=?", (job_id,)
    ).fetchone()
    conn.close()

    if not row or row[4] != "pending":
        return

    letter, emotions_json, keywords_json, refresh_token, _, send_method, discord_webhook, target_email = row
    emotions = json.loads(emotions_json)
    keywords = json.loads(keywords_json)

    if send_method == "discord":
        send_discord_message(job_id, discord_webhook, letter, emotions, keywords)
    elif send_method == "email":
        send_email_message(job_id, target_email, letter, emotions, keywords)
    else:
        send_kakao_message(job_id)


# ── APScheduler ─────────────────────────────────────────────
KST = timezone(timedelta(hours=9))

scheduler = BackgroundScheduler(timezone="Asia/Seoul", job_defaults={"misfire_grace_time": 300})
scheduler.start()

# ── FastAPI ─────────────────────────────────────────────────
app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


# ── STT ─────────────────────────────────────────────────────
def request_stt(audio_bytes: bytes) -> Optional[str]:
    endpoint = "https://eastus.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=ko-KR&format=detailed"
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("AZURE_SPEECH_KEY"),
        "Content-Type": "audio/wav",
    }
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        buf = io.BytesIO()
        audio.export(buf, format="wav")
        audio_bytes = buf.getvalue()
    except Exception as e:
        print(f"오디오 변환 오류: {e}")
        return None

    resp = requests.post(endpoint, headers=headers, data=audio_bytes)
    if resp.status_code != 200:
        print(f"STT 오류: {resp.status_code} {resp.text}")
        return None
    return resp.json().get("DisplayText")


# ── GPT ─────────────────────────────────────────────────────
PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", "당신은 사용자의 감정 일기를 분석해 미래의 자신에게 보내는 따뜻한 편지를 작성하는 AI입니다."),
    ("human", """오늘 하루의 감정과 생각:
"{text}"
{past_context}
다음 JSON 형식으로 정확히 응답해주세요 (JSON만, 다른 텍스트 없이):
{{
  "emotions": ["😊 기쁨", "🤔 고민"],
  "keywords": ["성장", "도전", "희망"],
  "letter": "미래의 나에게,\\n\\n[따뜻하고 진심 어린 200~300자 편지. 과거 기록이 있다면 자연스럽게 연결해주세요]\\n\\n과거의 나로부터"
}}
emotions: 오늘 감정 1~3가지 (이모지 포함)
keywords: 핵심 키워드 3~5가지
letter: 미래의 나에게 보내는 편지 (200~300자, 한국어)"""),
])


def get_llm():
    return AzureChatOpenAI(
        azure_deployment="gpt-4o",
        azure_endpoint="https://fimtrus-foundry10.cognitiveservices.azure.com/",
        api_key=os.getenv("AZURE_GPT_KEY"),
        api_version="2025-01-01-preview",
        temperature=0.8,
        max_tokens=1000,
    )


def request_gpt(text: str, kakao_id: str = "anonymous") -> Optional[dict]:
    # RAG: 해당 유저의 과거 편지만 검색
    try:
        search_filter = {"kakao_id": kakao_id} if kakao_id != "anonymous" else None
        past_docs = get_vectorstore().similarity_search(text, k=3, filter=search_filter)
    except Exception:
        past_docs = []

    past_context = ""
    if past_docs:
        past_context = "\n[과거 기록 - 아래 내용을 참고해 더 개인화된 편지를 써주세요]\n"
        past_context += "\n---\n".join(d.page_content for d in past_docs)

    # LangChain LCEL 체인: 프롬프트 → LLM → 문자열 파싱
    chain = PROMPT_TEMPLATE | get_llm() | StrOutputParser()

    try:
        content = chain.invoke({"text": text, "past_context": past_context})
        content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(content)
        # 생성된 편지를 해당 유저 ID와 함께 저장
        save_letter_to_vectorstore(
            text,
            result.get("letter", ""),
            result.get("emotions", []),
            result.get("keywords", []),
            kakao_id=kakao_id,
        )
        return result
    except Exception as e:
        print(f"GPT 오류: {e}")
        return None


# ── TTS ─────────────────────────────────────────────────────
def request_tts(text: str) -> Optional[bytes]:
    endpoint = "https://eastus.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
        "Ocp-Apim-Subscription-Key": os.getenv("AZURE_SPEECH_KEY"),
    }
    body = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ko-KR">
    <voice name="ko-KR-SunHiNeural">{text}</voice>
</speak>"""
    resp = requests.post(endpoint, headers=headers, data=body.encode("utf-8"))
    return resp.content if resp.status_code == 200 else None


# ── QR ──────────────────────────────────────────────────────
def create_qr_base64(text: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=8, border=3)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#3D2B1F", back_color="white").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ── API: 메인 처리 ───────────────────────────────────────────
@app.post("/api/process")
async def process(audio: UploadFile = File(...), state: str = Form(default="")):
    kakao_id = oauth_states.get(state, {}).get("kakao_id", "anonymous") if state else "anonymous"

    audio_bytes = await audio.read()

    stt_text = request_stt(audio_bytes)
    if not stt_text:
        return {"error": "음성 인식에 실패했습니다."}

    result = request_gpt(stt_text, kakao_id=kakao_id)
    if not result:
        return {"error": "GPT 분석에 실패했습니다.", "stt_text": stt_text}

    emotions = result.get("emotions", [])
    keywords = result.get("keywords", [])
    letter   = result.get("letter", "")

    tts_bytes = request_tts(letter)
    tts_b64   = base64.b64encode(tts_bytes).decode() if tts_bytes else None
    date_str  = datetime.now().strftime("%Y년 %m월 %d일")

    # 카드 DB 저장 (kakao_id 포함)
    card_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO cards (id, kakao_id, letter, emotions, keywords, date, created_at) VALUES (?,?,?,?,?,?,?)",
        (card_id, kakao_id, letter,
         json.dumps(emotions, ensure_ascii=False),
         json.dumps(keywords, ensure_ascii=False),
         date_str, datetime.now().isoformat())
    )
    conn.commit(); conn.close()

    card_url = f"{FRONTEND_URL}/card/{card_id}"
    qr_b64   = create_qr_base64(card_url)

    return {
        "stt_text": stt_text,
        "emotions": emotions,
        "keywords": keywords,
        "letter":   letter,
        "tts_b64":  tts_b64,
        "qr_b64":   qr_b64,
        "date":     date_str,
        "card_id":  card_id,
    }


# ── API: 카드 조회 ───────────────────────────────────────────
@app.get("/api/card/{card_id}")
def get_card(card_id: str):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT letter, emotions, keywords, date FROM cards WHERE id=?", (card_id,)
    ).fetchone()
    conn.close()
    if not row:
        return {"error": "카드를 찾을 수 없습니다."}
    letter, emotions_json, keywords_json, date = row
    return {
        "letter":   letter,
        "emotions": json.loads(emotions_json),
        "keywords": json.loads(keywords_json),
        "date":     date,
    }


# ── API: 카카오 OAuth ────────────────────────────────────────
@app.get("/api/kakao/auth-url")
def kakao_auth_url(state: str):
    url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_KEY}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=talk_message"
        f"&state={state}"
    )
    return {"url": url}


@app.get("/api/kakao/callback")
def kakao_callback(code: str = None, state: str = None, error: str = None, error_description: str = None):
    # 사용자가 로그인을 취소하거나 권한 오류가 발생한 경우
    if error:
        print(f"[Kakao] OAuth 오류: {error} - {error_description}")
        return HTMLResponse(f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><title>로그인 오류</title>
<style>
  body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background: #1a0f0a;
          display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
  .box {{ text-align: center; color: #f5ebe0; max-width: 400px; padding: 20px; }}
  .emoji {{ font-size: 48px; margin-bottom: 16px; }}
  p {{ color: #e07070; font-size: 14px; line-height: 1.6; }}
  code {{ background: #2a1a14; padding: 2px 8px; border-radius: 4px; color: #c4a882; font-size: 12px; }}
</style></head>
<body>
  <div class="box">
    <div class="emoji">❌</div>
    <h2 style="color:#f5ebe0">카카오 로그인 실패</h2>
    <p>오류: <code>{error}</code><br>{error_description or ''}</p>
    <p style="margin-top:16px;color:#8a7065">카카오 개발자 콘솔에서<br>Redirect URI 등록 및 카카오 로그인 활성화를 확인하세요.</p>
  </div>
</body></html>""")

    # 토큰 교환
    resp = requests.post("https://kauth.kakao.com/oauth/token", data={
        "grant_type":    "authorization_code",
        "client_id":     KAKAO_KEY,
        "client_secret": KAKAO_SECRET,
        "redirect_uri":  REDIRECT_URI,
        "code":          code,
    })

    if resp.status_code == 200:
        tokens  = resp.json()
        profile = fetch_kakao_profile(tokens["access_token"])
        kakao_id = profile.get("kakao_id", "")
        nickname = profile.get("nickname", "")
        if kakao_id:
            upsert_user(kakao_id, nickname)
        oauth_states[state] = {
            "access_token":  tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "kakao_id":      kakao_id,
            "nickname":      nickname,
        }
        print(f"[Kakao] 토큰 발급 성공: state={state} kakao_id={kakao_id} nickname={nickname}")
        return HTMLResponse("""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><title>로그인 완료</title>
<style>
  body { font-family: 'Apple SD Gothic Neo', sans-serif; background: #1a0f0a;
         display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
  .box { text-align: center; color: #f5ebe0; }
  .emoji { font-size: 48px; margin-bottom: 16px; }
  p { color: #c4a882; font-size: 15px; }
</style></head>
<body>
  <div class="box">
    <div class="emoji">✅</div>
    <h2>카카오 로그인 완료</h2>
    <p>이 창은 자동으로 닫힙니다</p>
  </div>
  <script>
    window.opener && window.opener.postMessage('kakao-auth-complete', '*');
    setTimeout(() => window.close(), 1500);
  </script>
</body></html>""")
    else:
        err_data = resp.json()
        err_code = err_data.get("error_code", "")
        err_msg  = err_data.get("error_description", resp.text)
        print(f"[Kakao] 토큰 교환 실패: {err_code} - {err_msg}")
        return HTMLResponse(f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><title>로그인 오류</title>
<style>
  body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background: #1a0f0a;
          display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
  .box {{ text-align: center; color: #f5ebe0; max-width: 420px; padding: 20px; }}
  .emoji {{ font-size: 48px; margin-bottom: 16px; }}
  p {{ color: #e07070; font-size: 14px; line-height: 1.8; }}
  code {{ background: #2a1a14; padding: 2px 8px; border-radius: 4px; color: #c4a882; font-size: 12px; }}
</style></head>
<body>
  <div class="box">
    <div class="emoji">❌</div>
    <h2 style="color:#f5ebe0">토큰 발급 실패</h2>
    <p>오류 코드: <code>{err_code}</code><br>{err_msg}</p>
    <p style="margin-top:16px;color:#8a7065">
      KOE006: Redirect URI 불일치<br>
      KOE008: 카카오 로그인 미활성화<br>
      → 개발자 콘솔에서 확인하세요
    </p>
  </div>
</body></html>""")


@app.get("/api/kakao/status/{state}")
def kakao_status(state: str):
    return {"authenticated": state in oauth_states}


@app.get("/api/me")
def get_me(state: str):
    info = oauth_states.get(state)
    if not info:
        return {"error": "인증 정보가 없습니다."}
    return {
        "kakao_id": info.get("kakao_id", ""),
        "nickname": info.get("nickname", ""),
    }


@app.get("/api/history")
def get_history(state: str):
    info = oauth_states.get(state)
    if not info or not info.get("kakao_id"):
        return {"error": "인증 정보가 없습니다."}
    kakao_id = info["kakao_id"]
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, letter, emotions, keywords, date, created_at FROM cards "
        "WHERE kakao_id=? ORDER BY created_at DESC LIMIT 50",
        (kakao_id,),
    ).fetchall()
    conn.close()
    return {
        "cards": [
            {
                "id":         r[0],
                "letter":     r[1],
                "emotions":   json.loads(r[2]),
                "keywords":   json.loads(r[3]),
                "date":       r[4],
                "created_at": r[5],
            }
            for r in rows
        ]
    }


# 프론트엔드 콜백(5173)에서 code 받아서 토큰 교환
@app.get("/api/kakao/exchange")
def kakao_exchange(code: str, state: str):
    resp = requests.post("https://kauth.kakao.com/oauth/token", data={
        "grant_type":    "authorization_code",
        "client_id":     KAKAO_KEY,
        "client_secret": KAKAO_SECRET,
        "redirect_uri":  REDIRECT_URI,
        "code":          code,
    })
    if resp.status_code == 200:
        tokens   = resp.json()
        profile  = fetch_kakao_profile(tokens["access_token"])
        kakao_id = profile.get("kakao_id", "")
        nickname = profile.get("nickname", "")
        if kakao_id:
            upsert_user(kakao_id, nickname)
        oauth_states[state] = {
            "access_token":  tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "kakao_id":      kakao_id,
            "nickname":      nickname,
        }
        print(f"[Kakao] 토큰 발급 성공: state={state} kakao_id={kakao_id} nickname={nickname}")
        return {"success": True}
    else:
        err = resp.json()
        print(f"[Kakao] 토큰 교환 실패: {err}")
        return {"success": False, "error": err.get("error_description", resp.text)}


# ── API: 예약 발송 ───────────────────────────────────────────
class ScheduleRequest(BaseModel):
    state:           Optional[str] = None
    send_method:     str = "kakao"        # kakao | discord | email
    discord_webhook: Optional[str] = None
    target_email:    Optional[str] = None
    letter:          str
    emotions:        List[str]
    keywords:        List[str]
    date_scheduled:  str                  # ISO 8601


@app.post("/api/schedule")
def schedule_message(data: ScheduleRequest):
    refresh_token = None
    kakao_id = "anonymous"

    if data.send_method == "kakao":
        if not data.state or data.state not in oauth_states:
            return {"error": "카카오 인증이 필요합니다."}
        refresh_token = oauth_states[data.state]["refresh_token"]
        kakao_id = oauth_states[data.state].get("kakao_id", "anonymous")
    elif data.send_method == "discord":
        if not data.discord_webhook:
            return {"error": "Discord 웹훅 URL을 입력해주세요."}
        kakao_id = oauth_states.get(data.state or "", {}).get("kakao_id", "anonymous")
    elif data.send_method == "email":
        if not data.target_email:
            return {"error": "이메일 주소를 입력해주세요."}
        kakao_id = oauth_states.get(data.state or "", {}).get("kakao_id", "anonymous")
    else:
        return {"error": "지원하지 않는 발송 채널입니다."}

    job_id   = str(uuid.uuid4())
    dt_utc   = datetime.fromisoformat(data.date_scheduled.replace("Z", "+00:00"))
    sched_dt = dt_utc.astimezone(KST).replace(tzinfo=None)
    is_immediate = (sched_dt - datetime.now()).total_seconds() < 60

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO schedules
           (id, kakao_id, letter, emotions, keywords, date_created, date_scheduled,
            refresh_token, status, send_method, discord_webhook, target_email)
           VALUES (?,?,?,?,?,?,?,?,'pending',?,?,?)""",
        (
            job_id,
            kakao_id,
            data.letter,
            json.dumps(data.emotions, ensure_ascii=False),
            json.dumps(data.keywords, ensure_ascii=False),
            datetime.now().isoformat(),
            data.date_scheduled,
            refresh_token,
            data.send_method,
            data.discord_webhook,
            data.target_email,
        )
    )
    conn.commit()
    conn.close()

    if is_immediate:
        # 즉시 발송: 스케줄러 없이 백그라운드 스레드에서 직접 실행
        threading.Thread(target=dispatch_message, args=[job_id], daemon=True).start()
    else:
        scheduler.add_job(
            dispatch_message,
            trigger=DateTrigger(run_date=sched_dt),
            args=[job_id],
            id=job_id,
            replace_existing=True,
        )

    return {
        "success":      True,
        "job_id":       job_id,
        "scheduled_at": data.date_scheduled,
    }


# ── API: 비밀 친구 챗봇 ──────────────────────────────────────
SYSTEM_PROMPT = """너는 '비밀 친구'야. Dear Me 서비스를 통해 오늘 하루를 기록한 사용자 곁에서
따뜻하게 공감하고 위로해주는 친구 같은 존재야.

대화 방식:
- 반말로 친근하게 대화해
- 사용자의 감정을 먼저 공감하고, 판단하지 마
- 너무 길게 말하지 말고 자연스럽게 주고받는 느낌으로
- 가끔 오늘 어땠는지, 무슨 생각이 드는지 부드럽게 물어봐
- 억지로 긍정적이려 하지 말고 솔직하게 공감해줘
- 이모지 1~2개 정도만 자연스럽게 써"""

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]

@app.post("/api/chat")
def chat(data: ChatRequest):
    endpoint = "https://fimtrus-foundry10.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview"
    headers  = {"api-key": os.getenv("AZURE_GPT_KEY"), "Content-Type": "application/json"}

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + data.messages

    resp = requests.post(endpoint, headers=headers, json={
        "messages": messages,
        "max_completion_tokens": 300,
        "temperature": 0.9,
    })
    if resp.status_code != 200:
        return {"error": "챗봇 응답에 실패했습니다."}

    content = resp.json()["choices"][0]["message"]["content"]
    return {"reply": content}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
