import os
import io
import json
import tempfile
import requests
import qrcode
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from dotenv import load_dotenv
from pydub import AudioSegment
import gradio as gr

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
AudioSegment.converter = "/Users/kimminyoung/opt/anaconda3/bin/ffmpeg"

FONT_PATH = "/System/Library/Fonts/AppleSDGothicNeo.ttc"


# ── Azure STT ──────────────────────────────────────────────
def request_stt(audio_path):
    endpoint = "https://eastus.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=ko-KR&format=detailed"
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("AZURE_SPEECH_KEY"),
        "Content-Type": "audio/wav",
    }
    try:
        audio = AudioSegment.from_file(audio_path)
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        buf = io.BytesIO()
        audio.export(buf, format="wav")
    except Exception as e:
        print(f"오디오 변환 오류: {e}")
        return None

    resp = requests.post(endpoint, headers=headers, data=buf.getvalue())
    if resp.status_code != 200:
        print(f"STT 오류: {resp.status_code} {resp.text}")
        return None
    return resp.json().get("DisplayText")


# ── Azure OpenAI GPT ───────────────────────────────────────
def request_gpt(text):
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
  "letter": "미래의 나에게,\\n\\n[따뜻하고 진심 어린 200~300자 편지. 오늘의 감정을 담아 미래의 자신에게 위로와 응원을 전하는 내용]\\n\\n"
}}

emotions: 오늘 감정 1~3가지 (이모지 포함)
keywords: 핵심 키워드 3~5가지
letter: 미래의 나에게 보내는 편지 (200~300자, 한국어)"""

    body = {
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": 1000,
        "temperature": 0.8,
    }
    resp = requests.post(endpoint, headers=headers, json=body)
    if resp.status_code != 200:
        print(f"GPT 오류: {resp.status_code} {resp.text}")
        return None

    content = resp.json()["choices"][0]["message"]["content"]
    try:
        content = content.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(content)
    except Exception as e:
        print(f"JSON 파싱 오류: {e}\n{content}")
        return None


# ── Azure TTS ──────────────────────────────────────────────
def request_tts(text):
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
        print(f"TTS 오류: {resp.status_code}")
        return None

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(resp.content)
    tmp.close()
    return tmp.name


# ── QR 생성 ────────────────────────────────────────────────
def create_qr(text):
    qr = qrcode.QRCode(version=1, box_size=8, border=3)
    qr.add_data(text)
    qr.make(fit=True)
    return qr.make_image(fill_color="#3D2B1F", back_color="white").convert("RGB")


# ── 카드 생성 ──────────────────────────────────────────────
def create_card(letter, emotions, keywords, date_str, qr_img):
    W, H = 900, 1200
    BG = "#FFF8F0"
    DARK = "#3D2B1F"
    MID = "#7A5C4F"
    LIGHT = "#C4A882"
    ACCENT = "#E8C5A0"

    card = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(card)

    def font(size):
        try:
            return ImageFont.truetype(FONT_PATH, size)
        except Exception:
            return ImageFont.load_default()

    # 테두리
    for i in range(3):
        draw.rectangle([12 + i, 12 + i, W - 12 - i, H - 12 - i], outline=LIGHT)

    # 헤더 배경
    draw.rectangle([0, 0, W, 160], fill=ACCENT)

    # 제목
    draw.text((W // 2, 55), "💌 Dear Me", fill=DARK, font=font(52), anchor="mm")
    draw.text((W // 2, 115), "미래의 나에게 보내는 타임캡슐", fill=MID, font=font(24), anchor="mm")

    # 날짜
    draw.text((W // 2, 185), f"📅  {date_str}", fill=MID, font=font(22), anchor="mm")

    # 감정 태그
    x = 50
    for emo in emotions:
        bbox = draw.textbbox((0, 0), emo, font=font(22))
        w = bbox[2] - bbox[0] + 24
        draw.rounded_rectangle([x, 215, x + w, 250], radius=12, fill=ACCENT, outline=LIGHT)
        draw.text((x + 12, 232), emo, fill=DARK, font=font(22), anchor="lm")
        x += w + 12

    # 키워드
    kw_text = "  #" + "  #".join(keywords)
    draw.text((50, 265), kw_text, fill=LIGHT, font=font(20))

    # 구분선
    draw.line([(50, 300), (W - 50, 300)], fill=ACCENT, width=2)

    # 편지 본문 (줄바꿈 처리)
    y = 325
    for paragraph in letter.split("\n"):
        words = paragraph.split(" ")
        line = ""
        for word in words:
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
        y += 8  # 문단 간격

    # QR 코드 (우하단)
    qr_size = 200
    qr_resized = qr_img.resize((qr_size, qr_size))
    card.paste(qr_resized, (W - qr_size - 50, H - qr_size - 80))
    draw.text((W - qr_size // 2 - 50, H - 58), "QR로 편지 보기", fill=MID, font=font(18), anchor="mm")

    # 하단 장식
    draw.text((55, H - 65), "✉️ Time Capsule", fill=LIGHT, font=font(20))

    return card


# ── 메인 처리 ──────────────────────────────────────────────
def process(audio_path):
    if audio_path is None:
        return "음성을 먼저 녹음해주세요.", "", None, None, None

    # 1. STT
    stt_text = request_stt(audio_path)
    if not stt_text:
        return "음성 인식에 실패했습니다. 다시 시도해주세요.", "", None, None, None

    # 2. GPT 분석
    result = request_gpt(stt_text)
    if not result:
        return stt_text, "GPT 분석에 실패했습니다.", None, None, None

    emotions = result.get("emotions", [])
    keywords = result.get("keywords", [])
    letter = result.get("letter", "")

    # 3. TTS
    tts_path = request_tts(letter)

    # 4. QR
    qr_img = create_qr(letter)

    # 5. 카드
    date_str = datetime.now().strftime("%Y년 %m월 %d일")
    card_img = create_card(letter, emotions, keywords, date_str, qr_img)

    return stt_text, letter, tts_path, qr_img, card_img


# ── Gradio UI ──────────────────────────────────────────────
with gr.Blocks(title="Dear Me 💌") as demo:
    gr.Markdown(
        """# 💌 Dear Me
        **오늘의 나를 기록하고, 미래의 나에게 편지를 보내세요.**
        말하기 → STT 변환 → GPT 편지 작성 → TTS 낭독 → QR + 카드 생성"""
    )

    with gr.Row():
        input_audio = gr.Audio(
            sources=["microphone"],
            type="filepath",
            label="🎤 오늘 하루 어땠나요? (녹음 후 정지 버튼)",
        )

    send_btn = gr.Button("💌 편지 만들기", variant="primary", size="lg")

    with gr.Row():
        stt_output = gr.Textbox(label="📝 인식된 내용", lines=3, interactive=False)
        letter_output = gr.Textbox(label="💌 미래의 나에게", lines=10, interactive=False)

    with gr.Row():
        audio_output = gr.Audio(label="🔊 편지 낭독", interactive=False, autoplay=True)
        qr_output = gr.Image(label="📱 QR 코드", width=220, interactive=False)

    card_output = gr.Image(label="🖨️ 타임캡슐 카드 (저장 가능)", interactive=False)

    send_btn.click(
        process,
        inputs=[input_audio],
        outputs=[stt_output, letter_output, audio_output, qr_output, card_output],
    )

demo.launch(theme=gr.themes.Soft())
