
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

SYSTEM_PROMPT = "너는 고민상담사야. 질문에 들어오면, 공감을 먼저해주고, 해결책을 제시하는 순서로 답변해줘. 글자수는 최대 300자 이내로 부탁해."

def chat(message, history):
    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": SYSTEM_PROMPT}]
        }
    ]

    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": message})

    completion = client.chat.completions.create(
        model=deployment,
        messages=messages,
        max_tokens=6553,
        temperature=0.7,
        top_p=0.95,
        stream=False
    )

    return completion.choices[0].message.content

with gr.Blocks(title="고민상담소") as demo:
    gr.Markdown("## 💬 고민상담소\n어떤 고민이든 편하게 말씀해 주세요. 공감하고 함께 해결책을 찾아드릴게요.")
    gr.ChatInterface(fn=chat)

demo.launch(share=True, theme=gr.themes.Soft())