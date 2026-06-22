"""
기업 공시 / 증권사 리포트 RAG 챗봇.
사용법: python ingest.py 실행 후 → python app.py
"""

import os
from dotenv import load_dotenv
import gradio as gr
from langchain_openai import ChatOpenAI
from embeddings import LocalEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

CHROMA_DIR = "./chroma_db"
TOP_K = 4  # 검색할 유사 문서 수

SYSTEM_PROMPT = """당신은 기업 공시 및 금융 리포트 전문 분석가입니다.
아래 컨텍스트(문서 발췌)를 바탕으로 질문에 정확하고 간결하게 답변하세요.
컨텍스트에 없는 내용은 "제공된 문서에서 해당 정보를 찾을 수 없습니다."라고 답하세요.
숫자나 수치가 있을 경우 반드시 포함해 주세요.

[컨텍스트]
{context}"""


def load_chain():
    embeddings = LocalEmbeddings()

    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.2,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
    ])

    doc_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, doc_chain)


rag_chain = None


def chat(question, history):
    global rag_chain
    if not question.strip():
        return history

    if rag_chain is None:
        if not os.path.exists(CHROMA_DIR):
            history.append({"role": "assistant", "content": "❌ ChromaDB가 없습니다. 먼저 터미널에서 `python ingest.py`를 실행하세요."})
            return history
        try:
            rag_chain = load_chain()
        except Exception as e:
            history.append({"role": "assistant", "content": f"❌ 초기화 오류: {e}"})
            return history

    try:
        result = rag_chain.invoke({"input": question})
    except Exception as e:
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": f"❌ 오류: {e}"})
        return history

    answer = result["answer"]

    # 출처 파일명 추출 (중복 제거)
    sources = list({
        os.path.basename(doc.metadata.get("source", ""))
        for doc in result["context"]
        if doc.metadata.get("source")
    })
    if sources:
        answer += f"\n\n📄 **출처**: {', '.join(sources)}"

    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    return history


def clear_chat():
    return []


with gr.Blocks(title="기업 공시 RAG 챗봇", theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 📊 기업 공시 / 증권사 리포트 RAG 챗봇")
    gr.Markdown(
        "**사용 순서:** `data/` 폴더에 PDF 또는 TXT 파일을 넣고 → "
        "`python ingest.py` 실행 → `python app.py` 실행"
    )

    chatbot = gr.Chatbot(height=500, type="messages", label="대화")

    with gr.Row():
        msg_box = gr.Textbox(
            placeholder="예: 삼성전자 2024년 영업이익은 얼마인가요?",
            label="질문",
            scale=8,
        )
        submit_btn = gr.Button("전송", variant="primary", scale=1)

    clear_btn = gr.Button("대화 초기화")

    submit_btn.click(chat, inputs=[msg_box, chatbot], outputs=[chatbot]).then(
        lambda: "", outputs=[msg_box]
    )
    msg_box.submit(chat, inputs=[msg_box, chatbot], outputs=[chatbot]).then(
        lambda: "", outputs=[msg_box]
    )
    clear_btn.click(clear_chat, outputs=[chatbot])

demo.launch(share=True)
