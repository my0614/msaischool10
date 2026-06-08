import os
import gradio as gr
import requests
from dotenv import load_dotenv

load_dotenv()

def request_stt(audio_path):
    endpoint = "https://eastus.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=ko-KR&format=detailed"
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("AZURE_SPEECH_KEY"),
        "Content-Type": "audio/wav",
    }

    with open(audio_path, "rb") as audio_file:
        audio_data = audio_file.read()

    body = audio_data

    response = requests.post(endpoint, headers=headers, data=body)
    response_json = response.json()
    display_text = response_json.get("DisplayText")
    masked_itn = response_json.get("NBest")[0]["MaskedITN"]
    return display_text
with gr.Blocks() as demo:

    def stop_recording(audio_path):
        text = request_stt(audio_path)
        return text

    gr.Markdown("# 음성 챗봇")

    chatbot = gr.Chatbot(label="음성 챗봇")
    
    with gr.Row():
        input_audio = gr.Audio(
            sources=["microphone"],
            type="filepath",
            label="음성 입력",
            scale=2
        )

        input_text = gr.Textbox(
            label="텍스트 입력",
            scale=4
        )

        submit_button = gr.Button(
            "전송",
            scale=1
        )

    output_audio = gr.Audio(
        label="음성 출력",
        interactive=False
    )

    input_audio.stop_recording(
        stop_recording,
        inputs=[input_audio],
        outputs=[input_text]
    )

demo.launch()