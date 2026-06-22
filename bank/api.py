"""
FastAPI 백엔드 - RAG 챗봇 API
사용법: venv/bin/uvicorn api:app --reload
접속:   http://localhost:8000
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

CHROMA_DIR = "./chroma_db"
rag_chain = None


def get_chain():
    global rag_chain
    if rag_chain is not None:
        return rag_chain

    from embeddings import LocalEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain_openai import ChatOpenAI
    from langchain.chains import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain_core.prompts import ChatPromptTemplate

    embeddings = LocalEmbeddings()
    vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.2,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 기업 공시 및 금융 리포트 전문 분석가입니다.
아래 컨텍스트를 바탕으로 질문에 정확하고 간결하게 답변하세요.
컨텍스트에 없는 내용은 "제공된 문서에서 해당 정보를 찾을 수 없습니다."라고 답하세요.
숫자나 수치가 있을 경우 반드시 포함해 주세요.

[컨텍스트]
{context}"""),
        ("human", "{input}"),
    ])

    doc_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, doc_chain)
    return rag_chain


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.question.strip():
        return ChatResponse(answer="질문을 입력해주세요.", sources=[])

    if not Path(CHROMA_DIR).exists():
        return ChatResponse(answer="❌ 먼저 터미널에서 `python ingest.py`를 실행해주세요.", sources=[])

    chain = get_chain()
    result = chain.invoke({"input": req.question})

    sources = list({
        os.path.basename(doc.metadata.get("source", ""))
        for doc in result["context"]
        if doc.metadata.get("source")
    })

    return ChatResponse(answer=result["answer"], sources=sources)
