{
  id: "dart-rag",
  type: "team",
  title: "기업 공시 RAG 분석 시스템",
  subtitle: "LangChain 기반 금융 문서 질의응답 서비스",
  company: "Team Project",
  initial: "D",
  summary: "DART 공시 및 증권사 리포트 PDF를 자동 수집·분석하여 자연어 질문에 답변하는 RAG(Retrieval-Augmented Generation) 시스템. LangChain으로 문서 파이프라인을 구성하고 HuggingFace 로컬 임베딩 모델과 ChromaDB 벡터 스토어를 연동해 비용 없이 문서 검색 인프라를 구축했습니다. FastAPI로 REST API를 제공하며 OpenAI GPT를 통해 컨텍스트 기반 답변을 생성합니다.",
  thumb: "/projects/dart_rag_thum.webp",
  image: { src: "/projects/dart_rag_thum.webp", caption: "기업 공시 RAG 챗봇 화면" },
  tags: ["LangChain", "ChromaDB", "FastAPI", "OpenAI API", "HuggingFace Transformers", "PyTorch", "DART API", "Python"],
  year: "2026.06",
  metrics: [
    { value: "5단계", label: "End-to-End 파이프라인", from: "수집→청킹→임베딩→검색→생성" },
    { value: "로컬", label: "HuggingFace 임베딩", from: "API 비용 Zero" },
    { value: "RAG", label: "LangChain 체인", from: "컨텍스트 기반 답변" },
  ],
  sections: {
    intent: [
      "기업 공시(DART)·증권사 리포트는 방대하고 비정형적 — 원하는 정보를 찾으려면 수십 페이지를 수동 탐색해야 함",
      "LLM 단독 사용 시 학습 데이터 미포함 최신 공시 정보는 답변 불가(할루시네이션 위험)",
      "RAG 구조로 실제 문서를 실시간 검색·주입해 최신 공시 기반의 정확한 답변 생성",
      "Azure 종속 없이 로컬 임베딩 모델(HuggingFace Transformers)로 임베딩 비용 완전 제거",
      "DART OpenAPI 연동으로 기업명 입력만으로 공시 PDF 자동 수집 — 수동 데이터 수집 단계 제거",
    ],
    tech: [
      {
        title: "LangChain 기반 RAG 파이프라인",
        description: "문서 로딩부터 답변 생성까지 LangChain으로 End-to-End 파이프라인 구성. create_retrieval_chain으로 검색-생성 단계를 단일 체인으로 연결",
        points: [
          "PyPDFLoader·TextLoader로 PDF·TXT 문서 로드, RecursiveCharacterTextSplitter로 500자 단위 청킹(중첩 50자)",
          "ChromaDB Retriever로 질문과 유사한 청크 Top-K 검색, ChatPromptTemplate으로 컨텍스트 주입",
          "create_stuff_documents_chain + create_retrieval_chain으로 검색→프롬프트→LLM 파이프라인 단일 체인 구성",
        ],
      },
      {
        title: "HuggingFace Transformers 로컬 임베딩",
        description: "sentence-transformers 의존성 없이 AutoTokenizer·AutoModel을 직접 활용한 커스텀 임베딩 클래스 구현. LangChain Embeddings 인터페이스 상속으로 벡터스토어와 완전 호환",
        points: [
          "transformers AutoModel + Mean Pooling + L2 정규화로 문장 임베딩 직접 구현",
          "langchain_core.embeddings.Embeddings 상속으로 LangChain 생태계와 호환",
          "paraphrase-multilingual-MiniLM-L12-v2 모델로 한국어 포함 다국어 지원, API 비용 Zero",
        ],
      },
      {
        title: "DART OpenAPI 공시 자동 수집 크롤러",
        description: "금융감독원 DART OpenAPI를 활용해 기업명만으로 최신 공시 PDF를 자동 수집. 전체 기업코드 매핑 및 정기공시 필터링으로 데이터 수집 자동화",
        points: [
          "DART corpCode API로 전체 상장기업 코드 매핑, 기업명 → corp_code 자동 변환",
          "정기공시(사업보고서·반기보고서) 필터링 후 원문 ZIP 다운로드 및 PDF 추출",
          "CLI 인터페이스(--corp, --count)로 기업명·수집건수 파라미터화",
        ],
      },
      {
        title: "FastAPI REST API 서버",
        description: "Gradio 종속 없이 FastAPI로 /chat 엔드포인트 구성. 정적 파일 서빙과 RAG 체인을 단일 서버에서 처리하며 RAG 체인은 첫 요청 시 지연 초기화(Lazy Loading)",
        points: [
          "POST /chat 엔드포인트로 질문 수신 → RAG 체인 실행 → 답변·출처 반환",
          "RAG 체인 Lazy Loading으로 서버 시작 시간 단축 및 메모리 효율화",
          "StaticFiles로 HTML 채팅 UI를 동일 서버에서 제공, 별도 프론트엔드 서버 불필요",
        ],
      },
    ],
    expect: [
      "금융 공시 탐색 시간 단축 — 수십 페이지 문서를 자연어 질문 하나로 즉시 요약·조회",
      "로컬 임베딩 모델 적용으로 임베딩 API 비용 제거, 대량 문서 처리 시 비용 우위 확보",
      "DART 크롤러 자동화로 최신 공시 데이터 상시 동기화 가능, 데이터 파이프라인 확장 기반 마련",
      "LangChain 표준 인터페이스 기반 설계로 임베딩 모델·LLM·벡터DB 교체 용이",
    ],
  },
}
