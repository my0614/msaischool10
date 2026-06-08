import os
import io
import tempfile
import requests
import sounddevice as sd
import soundfile as sf
import numpy as np
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.playback import play

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

AudioSegment.converter = "/Users/kimminyoung/opt/anaconda3/bin/ffmpeg"

SAMPLE_RATE = 16000
RECORD_SECONDS = 5


def record_audio():
    print("🎤 말씀하세요... (5초)")
    audio_data = sd.rec(
        int(SAMPLE_RATE * RECORD_SECONDS),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
    )
    sd.wait()
    print("녹음 완료")

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio_data, SAMPLE_RATE)
    return tmp.name


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
        audio_data = buf.getvalue()
    except Exception as e:
        print(f"STT 오디오 변환 오류: {e}")
        return None

    response = requests.post(endpoint, headers=headers, data=audio_data)
    if response.status_code != 200:
        print(f"STT 오류: {response.status_code}, {response.text}")
        return None

    return response.json().get("DisplayText")


def request_gpt(text):
    endpoint = "https://fimtrus-foundry10.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview"
    headers = {
        "Authorization": f"Bearer {os.getenv('AZURE_GPT_KEY')}",
        "Content-Type": "application/json",
    }
    body = {
        "messages": [{"role": "user", "content": text}],
        "max_completion_tokens": 800,
        "temperature": 0.7,
    }

    response = requests.post(endpoint, headers=headers, json=body)
    if response.status_code != 200:
        print(f"GPT 오류: {response.status_code}, {response.text}")
        return None

    return response.json()["choices"][0]["message"]["content"]


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

    response = requests.post(endpoint, headers=headers, data=body.encode("utf-8"))
    if response.status_code != 200:
        print(f"TTS 오류: {response.status_code}")
        return

    audio = AudioSegment.from_wav(io.BytesIO(response.content))
    play(audio)


if __name__ == "__main__":
    print("=== 음성 챗봇 시작 (종료: Ctrl+C) ===")
    while True:
        try:
            audio_path = record_audio()
            text = request_stt(audio_path)
            os.remove(audio_path)

            if not text:
                print("음성을 인식하지 못했습니다. 다시 말씀해주세요.\n")
                continue

            print(f"나: {text}")

            answer = request_gpt(text)
            if not answer:
                continue

            print(f"GPT: {answer}\n")
            request_tts(answer)

        except KeyboardInterrupt:
            print("\n종료합니다.")
            break
