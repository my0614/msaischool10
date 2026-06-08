import os
import gradio as gr
import requests
from dotenv import load_dotenv

load_dotenv()

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
    # method = "POST"
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("AZURE_SPEECH_KEY")
    }
    # (이하 STT API 요청 및 응답 처리 로직 생략)

with gr.Blocks() as demo:
    
    def stop_recording(audio_path):
        text = request_stt(audio_path)
        return text
        
    def click_submit(text, histories):
        content = request_gpt(text)
        histories.append({"role": "user", "content": text})
        histories.append({"role": "assistant", "content": content})
        return histories

    gr.Markdown("# 음성 챗봇")
    
    chatbot = gr.Chatbot(label="음성 챗봇")
    with gr.Row():
        input_audio = gr.Audio(
            sources=["microphone"], type="filepath", label="음성 입력", scale=2
        )
        input_text = gr.Textbox(label="텍스트 입력", scale=4)
        submit_button = gr.Button("전송", scale=1)
        
    output_audio = gr.Audio(label="음성 출력", interactive=False)
    
    input_audio.stop_recording(
        stop_recording, inputs=[input_audio], outputs=[input_text]
    )
    
    submit_button.click(click_submit, inputs=[input_text, chatbot], outputs=[chatbot])

demo.launch()