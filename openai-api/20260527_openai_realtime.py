import os
import asyncio
import base64
import numpy as np
import sounddevice as sd
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

SAMPLE_RATE = 24000
CHUNK_SAMPLES = 2400  # 100ms

deployment_name = os.getenv("TTS_DEPLOYMENT_NAME", "gpt-4o-mini-tts")
endpoint = os.getenv("TTS_ENDPOINT_URL")
base_url = endpoint.replace("https://", "wss://").rstrip("/") + "/openai/v1"
token = os.getenv("TTS_API_KEY", os.getenv("AZURE_OPENAI_API_KEY"))


async def main() -> None:
    client = AsyncOpenAI(websocket_base_url=base_url, api_key=token)
    audio_queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def mic_callback(indata, frames, time, status):
        pcm16 = (indata[:, 0] * 32767).astype(np.int16)
        loop.call_soon_threadsafe(audio_queue.put_nowait, pcm16.tobytes())

    async with client.realtime.connect(model=deployment_name) as connection:
        await connection.session.update(
            session={
                "type": "realtime",
                "instructions": "You are a helpful assistant. Respond conversationally.",
                "output_modalities": ["audio"],
                "audio": {
                    "input": {
                        "transcription": {"model": "whisper-1"},
                        "format": {"type": "audio/pcm", "rate": SAMPLE_RATE},
                        "turn_detection": {
                            "type": "server_vad",
                            "threshold": 0.5,
                            "prefix_padding_ms": 300,
                            "silence_duration_ms": 500,
                            "create_response": True,
                            "interrupt_response": False,
                        },
                    },
                    "output": {
                        "voice": "alloy",
                        "format": {"type": "audio/pcm", "rate": SAMPLE_RATE},
                    },
                },
            }
        )

        async def send_mic():
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                blocksize=CHUNK_SAMPLES,
                callback=mic_callback,
            ):
                print("🎤 마이크 켜짐. 말씀하세요... (Ctrl+C로 종료)")
                while True:
                    chunk = await audio_queue.get()
                    await connection.input_audio_buffer.append(
                        audio=base64.b64encode(chunk).decode()
                    )

        async def receive_events():
            output_audio = bytearray()
            async for event in connection:
                if event.type == "response.output_audio.delta":
                    output_audio.extend(base64.b64decode(event.delta))
                elif event.type == "response.output_audio_transcript.delta":
                    print(event.delta, end="", flush=True)
                elif event.type == "conversation.item.input_audio_transcription.completed":
                    print(f"\n[나]: {event.transcript}")
                elif event.type == "response.done":
                    if output_audio:
                        audio_array = np.frombuffer(output_audio, dtype=np.int16).astype(np.float32) / 32767
                        sd.play(audio_array, samplerate=SAMPLE_RATE)
                        sd.wait()
                    output_audio = bytearray()
                    print()
                elif event.type == "error":
                    print(f"\n[오류]: {event.error.message}")

        try:
            await asyncio.gather(send_mic(), receive_events())
        except KeyboardInterrupt:
            print("\n\n👋 종료합니다.")


if __name__ == "__main__":
    asyncio.run(main())
