import io
import os
import base64
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

DEPLOYMENT = os.getenv("DEPLOYMENT_NAME")


@st.cache_resource
def get_client():
    return AzureOpenAI(
        azure_endpoint=os.getenv("ENDPOINT_URL"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2025-01-01-preview",
    )


SYSTEM_PROMPT = """당신은 '척척박사'입니다! 어떤 질문이든 자신감 넘치고, 친절하며, 재미있게 설명해주는 만능 박사예요.
- 어려운 개념도 쉽고 재미있는 예시와 비유로 풀어서 설명합니다
- "척척박사가 알려드릴게요!", "오, 아주 좋은 질문이에요!" 같은 활기찬 표현을 자주 씁니다
- 설명할 때 단계별로 체계적으로, 번호나 항목을 활용해서 알려줍니다
- 이미지가 첨부되면 꼼꼼하게 분석하고 흥미로운 점을 짚어드립니다
- 마지막엔 "더 궁금한 점이 있으면 언제든지 물어보세요! 😊" 같은 친근한 마무리 멘트를 붙여주세요"""


def encode_image(uploaded_file) -> str:
    with Image.open(uploaded_file) as img:
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return "data:image/png;base64," + encoded


def build_api_messages(api_history: list, user_content) -> list:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # 최근 대화 3쌍(6개 메시지)만 포함
    recent = api_history[-6:]
    messages.extend(recent)
    messages.append({"role": "user", "content": user_content})
    return messages


# ── 페이지 설정 ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="척척박사 챗봇", page_icon="🎓", layout="wide")
st.title("🎓 척척박사 챗봇")
st.caption("무엇이든 물어보세요! 척척박사가 쉽고 재미있게 설명해드립니다. 이미지도 첨부할 수 있어요 📸")

# ── 세션 상태 초기화 ──────────────────────────────────────────────────────────
if "chat_display" not in st.session_state:
    st.session_state.chat_display = []
if "api_history" not in st.session_state:
    st.session_state.api_history = []

# ── 사이드바: 매개변수 + 이미지 업로드 ────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 매개변수 설정")
    st.markdown("슬라이더로 척척박사의 답변 스타일을 조절해보세요!")

    temperature = st.slider("🌡️ Temperature (창의성)", 0.0, 1.0, 0.8, 0.05,
                            help="높을수록 창의적·다양, 낮을수록 일관·정확")
    top_p = st.slider("🎲 Top P (다양성)", 0.0, 1.0, 0.9, 0.05,
                      help="어휘 선택 범위 조절")
    max_tokens = st.slider("📝 Max Tokens (답변 길이)", 100, 2000, 1000, 100,
                           help="최대 생성 토큰 수")

    st.divider()
    st.markdown("**🔢 대화 메모리:** 최근 3쌍")
    st.markdown("**🖼️ 지원 이미지:** PNG / JPG / WEBP / GIF")
    st.divider()

    uploaded_file = st.file_uploader(
        "🖼️ 이미지 첨부 (선택)",
        type=["png", "jpg", "jpeg", "webp", "gif"],
    )
    if uploaded_file:
        st.image(uploaded_file, caption="첨부된 이미지", use_container_width=True)

    st.divider()
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.chat_display = []
        st.session_state.api_history = []
        st.rerun()

# ── 대화 기록 출력 ─────────────────────────────────────────────────────────────
for msg in st.session_state.chat_display:
    with st.chat_message(msg["role"], avatar="🙋" if msg["role"] == "user" else "🎓"):
        if msg.get("image_bytes"):
            st.image(msg["image_bytes"], width=280)
        if msg.get("content"):
            st.markdown(msg["content"])

# ── 채팅 입력 ──────────────────────────────────────────────────────────────────
user_input = st.chat_input("궁금한 것을 입력하세요!")

if user_input:
    text = user_input.strip()
    image_data_url = None
    image_bytes = None

    if uploaded_file:
        uploaded_file.seek(0)
        image_data_url = encode_image(uploaded_file)
        uploaded_file.seek(0)
        image_bytes = uploaded_file.read()

    # 유저 메시지 화면 표시
    with st.chat_message("user", avatar="🙋"):
        if image_bytes:
            st.image(image_bytes, width=280)
        st.markdown(text)

    st.session_state.chat_display.append({
        "role": "user",
        "content": text,
        "image_bytes": image_bytes,
    })

    # API 메시지 구성
    api_parts = [{"type": "text", "text": text}]
    if image_data_url:
        api_parts.append({"type": "image_url", "image_url": {"url": image_data_url}})

    user_api_content = api_parts if len(api_parts) > 1 else text
    messages = build_api_messages(st.session_state.api_history, user_api_content)

    # 척척박사 응답 생성
    with st.chat_message("assistant", avatar="🎓"):
        with st.spinner("척척박사가 생각 중이에요..."):
            try:
                completion = get_client().chat.completions.create(
                    model=DEPLOYMENT,
                    messages=messages,
                    max_tokens=int(max_tokens),
                    temperature=temperature,
                    top_p=top_p,
                    stream=False,
                )
                response = completion.choices[0].message.content
            except Exception as e:
                response = f"⚠️ 오류가 발생했습니다: {str(e)}"
        st.markdown(response)

    # 히스토리 업데이트
    st.session_state.api_history.append({"role": "user", "content": user_api_content})
    st.session_state.api_history.append({"role": "assistant", "content": response})
    st.session_state.chat_display.append({"role": "assistant", "content": response})

    st.rerun()
