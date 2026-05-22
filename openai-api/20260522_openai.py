
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import gradio as gr

load_dotenv()

endpoint = os.getenv("ENDPOINT_URL")
deployment = os.getenv("DEPLOYMENT_NAME")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=subscription_key,
    api_version="2025-01-01-preview",
)

SYSTEM_PROMPT = "맛집 추천해주는 챗봇이야! 최소 3가지의 맛집을 소개해줘."

messages = [
    {
        "role": "system",
        "content": [{"type": "text", "text": SYSTEM_PROMPT}]
    }
]

def chat(message, history):
    messages.append({"role": "user", "content": message})

    completion = client.chat.completions.create(
        model=deployment,
        messages=messages,
        max_tokens=6553,
        temperature=0.7,
        top_p=0.95,
        stream=False
    )

    answer = completion.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})
    return answer

with gr.Blocks(title="맛집 추천 챗봇") as demo:
    gr.Markdown("## 🍽️ 맛집 추천 챗봇\n지역이나 음식 종류를 알려주시면 맛집을 추천해드려요!")
    gr.ChatInterface(fn=chat)

demo.launch(share=True, theme=gr.themes.Soft())
    
   