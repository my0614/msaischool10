"""
PDF/TXT 문서를 로드하고 청킹 후 ChromaDB에 임베딩 저장.
사용법: python ingest.py
"""

import os
import glob
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from embeddings import LocalEmbeddings

load_dotenv()

DATA_DIR = "./data"
CHROMA_DIR = "./chroma_db"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def load_documents():
    docs = []

    pdf_files = glob.glob(f"{DATA_DIR}/**/*.pdf", recursive=True)
    for path in pdf_files:
        loader = PyPDFLoader(path)
        pages = loader.load()
        docs.extend(pages)
        print(f"[PDF] {path} → {len(pages)}페이지 로드")

    txt_files = glob.glob(f"{DATA_DIR}/**/*.txt", recursive=True)
    for path in txt_files:
        loader = TextLoader(path, encoding="utf-8")
        pages = loader.load()
        docs.extend(pages)
        print(f"[TXT] {path} → {len(pages)}청크 로드")

    return docs


def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"\n청크 생성 완료: 총 {len(chunks)}개 (크기={CHUNK_SIZE}, 중첩={CHUNK_OVERLAP})")
    return chunks


def build_vectorstore(chunks):
    embeddings = LocalEmbeddings()

    print("ChromaDB에 임베딩 저장 중...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
    )
    print(f"저장 완료: {CHROMA_DIR}/ ({len(chunks)}개 청크)")
    return vectorstore


if __name__ == "__main__":
    print("=== 문서 수집 및 벡터 저장 시작 ===\n")

    docs = load_documents()
    if not docs:
        print(f"⚠️  data/ 폴더에 PDF 또는 TXT 파일을 넣어주세요.")
        exit(1)

    print(f"\n총 {len(docs)}개 페이지/섹션 로드")
    chunks = split_documents(docs)
    build_vectorstore(chunks)

    print("\n=== 완료! 이제 app.py를 실행하세요 ===")
