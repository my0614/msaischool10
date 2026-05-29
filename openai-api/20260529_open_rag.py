
import os
import gradio as gr
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("ENDPOINT_URL")
deployment = os.getenv("DEPLOYMENT_NAME")
search_endpoint = os.getenv("SEARCH_ENDPOINT", "https://10ai003-search.search.windows.net")
search_key = os.getenv("SERACH_AI_KEY")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")

INDEX_OPTIONS = {
    "요리 레시피": {"index": "index-10ai003food",   "in_scope": True,  "strictness": 3},
    "여행 정보":   {"index": "index-10ai003travel",  "in_scope": False, "strictness": 1},
    "영화 정보":   {"index": "rag-1780035521025",    "in_scope": False, "strictness": 1},
}

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=subscription_key,
    api_version="2025-01-01-preview",
)

def chat(user_message, index_label, history):
    config = INDEX_OPTIONS[index_label]

    messages = [{"role": "system", "content": f"{index_label} 관련 도우미야. 친절하게 답변해줘."}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    completion = client.chat.completions.create(
        model=deployment,
        messages=messages,
        max_tokens=2000,
        temperature=0.7,
        stream=False,
        extra_body={
            "data_sources": [{
                "type": "azure_search",
                "parameters": {
                    "endpoint": search_endpoint,
                    "index_name": config["index"],
                    "query_type": "simple",
                    "fields_mapping": {},
                    "in_scope": config["in_scope"],
                    "filter": None,
                    "strictness": config["strictness"],
                    "top_n_documents": 5,
                    "authentication": {
                        "type": "api_key",
                        "key": search_key
                    }
                }
            }]
        }
    )

    answer = completion.choices[0].message.content
    citations = completion.choices[0].message.context.get("citations", [])
    filepaths = list({c["filepath"] for c in citations if c.get("filepath")})
    if filepaths:
        answer += f"\n\n📄 출처: {', '.join(filepaths)}"

    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": answer})
    return "", history

with gr.Blocks(title="RAG 챗봇") as demo:
    gr.Markdown("## Azure Search RAG 챗봇")

    index_selector = gr.Radio(
        choices=list(INDEX_OPTIONS.keys()),
        value="요리 레시피",
        label="인덱스 선택",
    )

    chatbot = gr.Chatbot(height=500)
    msg = gr.Textbox(placeholder="질문을 입력하세요...", label="메시지")

    with gr.Row():
        submit_btn = gr.Button("전송", variant="primary")
        clear_btn = gr.Button("초기화")

    index_selector.change(lambda: ([], ""), outputs=[chatbot, msg])

    submit_btn.click(chat, inputs=[msg, index_selector, chatbot], outputs=[msg, chatbot])
    msg.submit(chat, inputs=[msg, index_selector, chatbot], outputs=[msg, chatbot])
    clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])

demo.launch(share=True)
