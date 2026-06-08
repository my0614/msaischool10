import os
import io
import json
import base64
import tempfile
import requests
import qrcode
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from dotenv import load_dotenv
from pydub import AudioSegment
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
AudioSegment.converter = "/Users/kimminyoung/opt/anaconda3/bin/ffmpeg"
FONT_PATH = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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


def request_gpt(text: str) -> dict | None:
    endpoint = "https://fimtrus-foundry10.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview"
    headers = {
        "Authorization": f"Bearer {os.getenv('AZURE_GPT_KEY')}",
        "Content-Type": "application/json",
    }
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
    if resp.status_code != 200:
        return None
    return resp.content


def create_qr_base64(text: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=8, border=3)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#3D2B1F", back_color="white").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def create_card_base64(letter, emotions, keywords, date_str, qr_b64) -> str:
    W, H = 900, 1200
    BG, DARK, MID, LIGHT, ACCENT = "#FFF8F0", "#3D2B1F", "#7A5C4F", "#C4A882", "#E8C5A0"
    card = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(card)

    def font(size):
        try:
            return ImageFont.truetype(FONT_PATH, size)
        except Exception:
            return ImageFont.load_default()

    for i in range(3):
        draw.rectangle([12+i, 12+i, W-12-i, H-12-i], outline=LIGHT)
    draw.rectangle([0, 0, W, 160], fill=ACCENT)
    draw.text((W//2, 60), "💌 Dear Me", fill=DARK, font=font(52), anchor="mm")
    draw.text((W//2, 118), "미래의 나에게 보내는 타임캡슐", fill=MID, font=font(24), anchor="mm")
    draw.text((W//2, 185), f"📅  {date_str}", fill=MID, font=font(22), anchor="mm")

    x = 50
    for emo in emotions:
        bbox = draw.textbbox((0, 0), emo, font=font(22))
        w = bbox[2] - bbox[0] + 24
        draw.rounded_rectangle([x, 215, x+w, 252], radius=12, fill=ACCENT, outline=LIGHT)
        draw.text((x+12, 233), emo, fill=DARK, font=font(22), anchor="lm")
        x += w + 12

    draw.text((50, 266), "  #" + "  #".join(keywords), fill=LIGHT, font=font(20))
    draw.line([(50, 302), (W-50, 302)], fill=ACCENT, width=2)

    y = 328
    for paragraph in letter.split("\n"):
        line = ""
        for word in paragraph.split(" "):
            test = line + word + " "
            if draw.textbbox((0, 0), test, font=font(22))[2] > W - 100:
                draw.text((60, y), line.rstrip(), fill=DARK, font=font(22))
                y += 36
                line = word + " "
            else:
                line = test
        if line.strip():
            draw.text((60, y), line.rstrip(), fill=DARK, font=font(22))
            y += 36
        y += 8

    qr_size = 200
    qr_img = Image.open(io.BytesIO(base64.b64decode(qr_b64))).resize((qr_size, qr_size))
    card.paste(qr_img, (W - qr_size - 50, H - qr_size - 80))
    draw.text((W - qr_size//2 - 50, H - 55), "QR로 편지 보기", fill=MID, font=font(18), anchor="mm")
    draw.text((55, H - 65), "✉️ Time Capsule", fill=LIGHT, font=font(20))

    buf = io.BytesIO()
    card.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


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
    letter = result.get("letter", "")

    tts_bytes = request_tts(letter)
    tts_b64 = base64.b64encode(tts_bytes).decode() if tts_bytes else None

    qr_b64 = create_qr_base64(letter)
    date_str = datetime.now().strftime("%Y년 %m월 %d일")
    card_b64 = create_card_base64(letter, emotions, keywords, date_str, qr_b64)

    return {
        "stt_text": stt_text,
        "emotions": emotions,
        "keywords": keywords,
        "letter": letter,
        "tts_b64": tts_b64,
        "qr_b64": qr_b64,
        "card_b64": card_b64,
        "date": date_str,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
