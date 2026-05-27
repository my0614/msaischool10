import os
import io
import tempfile
import gradio as gr
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("TTS_API_KEY", os.getenv("AZURE_OPENAI_API_KEY")),
    api_version="2025-01-01-preview",
    azure_endpoint=os.getenv("TTS_ENDPOINT_URL", os.getenv("ENDPOINT_URL")),
)

TTS_DEPLOYMENT = os.getenv("TTS_DEPLOYMENT_NAME", "gpt-4o-mini-tts")

VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]


def text_to_speech(text: str, voice: str, speed: float) -> str:
    if not text.strip():
        raise gr.Error("텍스트를 입력해주세요.")

    response = client.audio.speech.create(
        model=TTS_DEPLOYMENT,
        voice=voice,
        input=text,
        speed=speed,
    )

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.write(response.content)
    tmp.close()
    return tmp.name


with gr.Blocks(title="Azure OpenAI TTS", theme=gr.themes.Soft()) as demo:
    gr.Markdown("## Azure OpenAI TTS (Text-to-Speech)")
    gr.Markdown("텍스트를 입력하고 목소리를 선택하면 음성을 생성합니다.")

    with gr.Row():
        with gr.Column(scale=2):
            text_input = gr.Textbox(
                label="텍스트 입력",
                placeholder="여기에 변환할 텍스트를 입력하세요...",
                lines=6,
            )
            with gr.Row():
                voice_select = gr.Dropdown(
                    label="목소리",
                    choices=VOICES,
                    value="alloy",
                )
                speed_slider = gr.Slider(
                    label="속도",
                    minimum=0.25,
                    maximum=4.0,
                    value=1.0,
                    step=0.25,
                )
            generate_btn = gr.Button("음성 생성", variant="primary")

        with gr.Column(scale=1):
            audio_output = gr.Audio(label="생성된 음성", type="filepath")

    generate_btn.click(
        fn=text_to_speech,
        inputs=[text_input, voice_select, speed_slider],
        outputs=audio_output,
    )

    gr.Examples(
        examples=[
            ["안녕하세요! Azure OpenAI TTS 데모입니다.", "alloy", 1.0],
            ["The quick brown fox jumped over the lazy dog.", "nova", 1.0],
            ["인공지능 기술이 빠르게 발전하고 있습니다.", "shimmer", 0.75],
        ],
        inputs=[text_input, voice_select, speed_slider],
    )

if __name__ == "__main__":
    demo.launch()
