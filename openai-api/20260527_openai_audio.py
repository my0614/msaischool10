import os
import io
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("STT_API_KEY"),
    api_version="2024-06-01",
    azure_endpoint=os.getenv("ENDPOINT_URL")
)

DEPLOYMENT_ID = "whisper"
SAMPLERATE = 16000


def record_audio(duration: int = 5) -> bytes:
    print(f"{duration}초 동안 녹음합니다... 말씀해주세요!")
    audio = sd.rec(int(duration * SAMPLERATE), samplerate=SAMPLERATE, channels=1, dtype="int16")
    sd.wait()
    print("✅ 녹음 완료!")

    # WAV 형식으로 메모리에 저장
    buf = io.BytesIO()
    wav.write(buf, SAMPLERATE, audio)
    buf.seek(0)
    return buf


def transcribe(audio_source) -> str:
    result = client.audio.transcriptions.create(
        file=("audio.wav", audio_source, "audio/wav"),
        model=DEPLOYMENT_ID,
        language="ko",
    )
    return result.text


if __name__ == "__main__":
    while True:
        try:
            sec = input("\n⏱️ 녹음 시간(초)을 입력하세요 (기본 5초, 종료: q): ").strip()
            if sec.lower() == "q":
                print("👋 종료합니다.")
                break

            duration = int(sec) if sec.isdigit() else 5
            audio_buf = record_audio(duration)

            print("🔄 Whisper로 변환 중...")
            text = transcribe(audio_buf)
            print(f"\n📝 변환 결과: {text}")

        except KeyboardInterrupt:
            print("\n👋 종료합니다.")
            break
