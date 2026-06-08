import os
import io
import gradio as gr
import requests
from dotenv import load_dotenv
from pydub import AudioSegment

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

AudioSegment.converter = "/Users/kimminyoung/opt/anaconda3/bin/ffmpeg"


def request_tts(text):
    endpoint = "https://eastus.tts.speech.microsoft.com/cognitiveservices/v1"
    # POST
    headers = {
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "riff-8khz-16bit-mono-pcm",
        "Ocp-Apim-Subscription-Key": os.getenv("AZURE_SPEECH_KEY"),
    }

    body = f"""
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
xmlns:mstts="http://www.w3.org/2001/10/synthesis" xml:lang="ko-KR">
    <voice name="ko-KR-SunHi:DragonHDLatestNeural">
        {text}
    </voice>
</speak>
"""

    response = requests.post(endpoint, headers=headers, data=body)

    import datetime

    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = "output_{}.wav".format(now)

    with open(file_name, "wb") as audio_file:
        audio_file.write(response.content)

    return file_name

def request_gpt(text):
    endpoint = "https://fimtrus-foundry10.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview"
    headers = {
        "Authorization": f"Bearer {os.getenv('AZURE_GPT_KEY')}"
    }
    body = {
        "messages": [{"role": "user", "content": text}],
        "max_completion_tokens": 800,
        "temperature": 0.7,
        "top_p": 0.95,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }
    
    response = requests.post(endpoint, headers=headers, json=body)
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return f"API 오류가 발생했습니다. (status: {response.status_code})"
        
    response_json = response.json()
    content = response_json["choices"][0]["message"]["content"]
    return content

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
        return ""

    response = requests.post(endpoint, headers=headers, data=audio_data)
    if response.status_code != 200:
        return ""

    response_json = response.json()
    return response_json.get("DisplayText", "")

with gr.Blocks() as demo:

    def stop_recording(audio_path):
        if audio_path is None:
            return ""
        text = request_stt(audio_path)
        return text

    def click_submit(text, histories):
        content = request_gpt(text)
        histories.append({"role": "user", "content": text})
        histories.append({"role": "assistant", "content": content})

        file_name = request_tts(content)
        return histories, file_name

    gr.Markdown("# 음성 챗봇")

    chatbot = gr.Chatbot(label="음성 챗봇")
    with gr.Row():
        input_audio = gr.Audio(
            sources=["microphone"], type="filepath", label="음성 입력", scale=2
        )
        input_text = gr.Textbox(label="텍스트 입력", scale=4)
        submit_button = gr.Button("전송", scale=1)

    output_audio = gr.Audio(
        label="음성 출력", interactive=False, autoplay=True
    )

    input_audio.stop_recording(
        stop_recording, inputs=[input_audio], outputs=[input_text]
    )

    submit_button.click(
        click_submit,
        inputs=[input_text, chatbot],
        outputs=[chatbot, output_audio],
    )

demo.launch()