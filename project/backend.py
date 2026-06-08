import os
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
from PIL import Image
from datetime import datetime
from dotenv import load_dotenv
from pydub import AudioSegment
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
AudioSegment.converter = "/Users/kimminyoung/opt/anaconda3/bin/ffmpeg"

KAKAO_KEY     = os.getenv("KAKAO_REST_API_KEY")
REDIRECT_URI  = "http://localhost:8000/api/kakao/callback"
DB_PATH       = os.path.join(os.path.dirname(__file__), "schedules.db")

# 카카오 OAuth 상태 임시 저장 (메모리)
oauth_states: dict = {}

# ── DB 초기화 ───────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id              TEXT PRIMARY KEY,
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
    ]:
        try:
            conn.execute(f"ALTER TABLE schedules ADD COLUMN {col} {typ}")
        except sqlite3.OperationalError:
            pass
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
            "title": "💌 미래의 나에게 | Dear Me",
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

    letter_html = letter.replace("\n", "<br>")
    keywords_str = "  ".join(f"#{k}" for k in keywords)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "💌 미래의 나에게 - Dear Me"
    msg["From"]    = smtp_user
    msg["To"]      = to_email

    html = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<style>
  body{{font-family:'Noto Serif KR',Georgia,serif;background:#f5e8d0;margin:0;padding:20px}}
  .card{{max-width:560px;margin:0 auto;background:linear-gradient(160deg,#FDF6EC,#F5E8D0);
         border-radius:20px;padding:48px 44px 40px;border:1px solid #E8D5B0}}
  .top{{text-align:center;color:#C4985A;font-size:11px;letter-spacing:3px;margin-bottom:28px}}
  .title{{text-align:center;font-size:38px;font-weight:300;color:#2C1A0E;margin:0 0 8px}}
  .date{{text-align:center;color:#7A5C3A;font-size:12px;letter-spacing:1px;margin-bottom:20px}}
  .tags{{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-bottom:10px}}
  .tag{{background:rgba(196,152,90,.12);border:1px solid #E8D5B0;border-radius:20px;
        padding:4px 12px;font-size:14px;color:#2C1A0E}}
  .kws{{text-align:center;color:#C4985A;font-size:12px;margin-bottom:28px}}
  .divider{{text-align:center;color:#E8D5B0;margin-bottom:24px}}
  .letter{{font-size:14px;line-height:2.1;color:#3a2510;background:rgba(255,255,255,.45);
           border-radius:12px;padding:20px 24px;border:1px solid rgba(232,213,176,.6)}}
  .footer{{text-align:center;margin-top:28px;color:#C4985A;font-size:10px;letter-spacing:2px}}
</style></head>
<body>
  <div class="card">
    <div class="top">✦ TIME CAPSULE ✦</div>
    <div class="title">💌 Dear Me</div>
    <div class="date">{datetime.now().strftime("%Y년 %m월 %d일")}</div>
    <div class="tags">{"".join(f'<span class="tag">{e}</span>' for e in emotions)}</div>
    <div class="kws">{keywords_str}</div>
    <div class="divider">─── ✦ ───</div>
    <div class="letter">{letter_html}</div>
    <div class="footer">✦ Time Capsule Letter ✦</div>
  </div>
</body></html>"""

    msg.attach(MIMEText(html, "html", "utf-8"))
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
scheduler = BackgroundScheduler(timezone="Asia/Seoul")
scheduler.start()

# ── FastAPI ─────────────────────────────────────────────────
app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


# ── STT ─────────────────────────────────────────────────────
def request_stt(audio_bytes: bytes) -> str | None:
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
def request_gpt(text: str) -> dict | None:
    endpoint = "https://fimtrus-foundry10.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview"
    headers = {"Authorization": f"Bearer {os.getenv('AZURE_GPT_KEY')}", "Content-Type": "application/json"}
    prompt = f"""사용자가 오늘 하루의 감정과 생각을 말했습니다:
"{text}"

다음 JSON 형식으로 정확히 응답해주세요 (다른 텍스트 없이 JSON만):
{{
  "emotions": ["😊 기쁨", "🤔 고민"],
  "keywords": ["성장", "도전", "희망"],
  "letter": "미래의 나에게,\\n\\n[따뜻하고 진심 어린 200~300자 편지]\\n\\n과거의 나로부터"
}}

emotions: 오늘 감정 1~3가지 (이모지 포함)
keywords: 핵심 키워드 3~5가지
letter: 미래의 나에게 보내는 편지 (200~300자, 한국어)"""

    resp = requests.post(endpoint, headers=headers, json={
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": 1000,
        "temperature": 0.8,
    })
    if resp.status_code != 200:
        print(f"GPT 오류: {resp.status_code}")
        return None

    content = resp.json()["choices"][0]["message"]["content"]
    try:
        content = content.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(content)
    except Exception as e:
        print(f"JSON 파싱 오류: {e}")
        return None


# ── TTS ─────────────────────────────────────────────────────
def request_tts(text: str) -> bytes | None:
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
async def process(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()

    stt_text = request_stt(audio_bytes)
    if not stt_text:
        return {"error": "음성 인식에 실패했습니다."}

    result = request_gpt(stt_text)
    if not result:
        return {"error": "GPT 분석에 실패했습니다.", "stt_text": stt_text}

    emotions = result.get("emotions", [])
    keywords = result.get("keywords", [])
    letter   = result.get("letter", "")

    tts_bytes = request_tts(letter)
    tts_b64   = base64.b64encode(tts_bytes).decode() if tts_bytes else None
    qr_b64    = create_qr_base64(letter)
    date_str  = datetime.now().strftime("%Y년 %m월 %d일")

    return {
        "stt_text": stt_text,
        "emotions": emotions,
        "keywords": keywords,
        "letter":   letter,
        "tts_b64":  tts_b64,
        "qr_b64":   qr_b64,
        "date":     date_str,
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
def kakao_callback(code: str, state: str):
    resp = requests.post("https://kauth.kakao.com/oauth/token", data={
        "grant_type":   "authorization_code",
        "client_id":    KAKAO_KEY,
        "redirect_uri": REDIRECT_URI,
        "code":         code,
    })
    if resp.status_code == 200:
        tokens = resp.json()
        oauth_states[state] = {
            "access_token":  tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        }

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


@app.get("/api/kakao/status/{state}")
def kakao_status(state: str):
    return {"authenticated": state in oauth_states}


# ── API: 예약 발송 ───────────────────────────────────────────
class ScheduleRequest(BaseModel):
    state:           str | None = None
    send_method:     str = "kakao"        # kakao | discord | email
    discord_webhook: str | None = None
    target_email:    str | None = None
    letter:          str
    emotions:        list[str]
    keywords:        list[str]
    date_scheduled:  str                  # ISO 8601


@app.post("/api/schedule")
def schedule_message(data: ScheduleRequest):
    refresh_token = None

    if data.send_method == "kakao":
        if not data.state or data.state not in oauth_states:
            return {"error": "카카오 인증이 필요합니다."}
        refresh_token = oauth_states[data.state]["refresh_token"]
    elif data.send_method == "discord":
        if not data.discord_webhook:
            return {"error": "Discord 웹훅 URL을 입력해주세요."}
    elif data.send_method == "email":
        if not data.target_email:
            return {"error": "이메일 주소를 입력해주세요."}
    else:
        return {"error": "지원하지 않는 발송 채널입니다."}

    job_id   = str(uuid.uuid4())
    sched_dt = datetime.fromisoformat(data.date_scheduled)

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO schedules
           (id, letter, emotions, keywords, date_created, date_scheduled,
            refresh_token, status, send_method, discord_webhook, target_email)
           VALUES (?,?,?,?,?,?,?,'pending',?,?,?)""",
        (
            job_id,
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
