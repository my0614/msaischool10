import io
import os
import base64
import gradio as gr
from PIL import Image
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

endpoint = os.getenv("ENDPOINT_URL")
deployment = os.getenv("DEPLOYMENT_NAME")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")

if not all([endpoint, deployment, subscription_key]):
    raise ValueError("⚠️ .env 파일에서 환경 변수를 불러오지 못했습니다.")

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=subscription_key,
    api_version="2025-01-01-preview",
)

SYSTEM_PROMPT = """당신은 '척척박사'입니다! 어떤 질문이든 자신감 넘치고, 친절하며, 재미있게 설명해주는 만능 박사예요.
- 어려운 개념도 쉽고 재미있는 예시와 비유로 풀어서 설명합니다
- "척척박사가 알려드릴게요!", "오, 아주 좋은 질문이에요!" 같은 활기찬 표현을 자주 씁니다
- 설명할 때 단계별로 체계적으로, 번호나 항목을 활용해서 알려줍니다
- 이미지가 첨부되면 꼼꼼하게 분석하고 흥미로운 점을 짚어드립니다
- 마지막엔 "더 궁금한 점이 있으면 언제든지 물어보세요! 😊" 같은 친근한 마무리 멘트를 붙여주세요"""


def encode_image(file_path: str) -> str:
    with Image.open(file_path) as img:
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return "data:image/png;base64," + encoded


def user_submit(message, chatbot, api_history):
    text = (message.get("text") or "").strip()
    files = message.get("files") or []

    if not text and not files:
        return chatbot, api_history, gr.MultimodalTextbox(value=None)

    # ── 챗봇 화면 표시용 ──────────────────────────────────────────────────────
    # Gradio 6.x MessageContent = Union[str, FileDataDict, ...]
    # content는 MessageContent 또는 list[MessageContent]
    display_content: list = []
    if text:
        display_content.append(text)
    for f in files:
        display_content.append({"path": f})  # FileDataDict 형식

    chatbot_content = display_content if len(display_content) > 1 else display_content[0]
    chatbot.append({"role": "user", "content": chatbot_content})

    # ── API 호출용 (base64 인코딩) ──────────────────────────────────────────
    api_parts = []
    if text:
        api_parts.append({"type": "text", "text": text})
    for f in files:
        api_parts.append({"type": "image_url", "image_url": {"url": encode_image(f)}})

    api_content = api_parts if len(api_parts) > 1 else (text if (text and not files) else api_parts[0])
    api_history.append({"role": "user", "content": api_content})

    return chatbot, api_history, gr.MultimodalTextbox(value=None)


def bot_respond(chatbot, api_history, temperature, top_p, max_tokens):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 최근 대화 3쌍(6개 메시지)만 포함
    recent = api_history[-6:] if len(api_history) > 6 else api_history
    messages.extend(recent)

    try:
        completion = client.chat.completions.create(
            model=deployment,
            messages=messages,
            max_tokens=int(max_tokens),
            temperature=temperature,
            top_p=top_p,
            stream=False,
        )
        response = completion.choices[0].message.content
    except Exception as e:
        response = f"⚠️ 오류가 발생했습니다: {str(e)}"

    chatbot.append({"role": "assistant", "content": response})
    api_history.append({"role": "assistant", "content": response})

    return chatbot, api_history


# ── UI ────────────────────────────────────────────────────────────────────────
with gr.Blocks(title="척척박사 챗봇") as demo:
    gr.Markdown(
        """
        # 🎓 척척박사 챗봇
        **무엇이든 물어보세요!** 척척박사가 쉽고 재미있게 설명해드립니다.
        이미지를 첨부하면 꼼꼼하게 분석해드려요 📸 &nbsp;|&nbsp; 대화 내역은 최근 **3쌍**만 기억합니다.
        """
    )

    api_history = gr.State([])

    with gr.Row():
        # ── 채팅 영역 ──────────────────────────────────────────────────────────
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                height=520,
                label="💬 대화창",
                buttons=["copy"],
                layout="bubble",
            )
            msg_input = gr.MultimodalTextbox(
                placeholder="궁금한 것을 입력하거나, 이미지를 드래그해서 첨부해보세요! 📎",
                file_types=["image"],
                lines=2,
                show_label=False,
                submit_btn=True,
            )
            clear_btn = gr.Button("🗑️ 대화 초기화", variant="secondary", size="sm")

        # ── 매개변수 패널 ──────────────────────────────────────────────────────
        with gr.Column(scale=1, min_width=220):
            gr.Markdown("### ⚙️ 매개변수 설정")
            gr.Markdown("슬라이더로 척척박사의 답변 스타일을 조절해보세요!")
            temperature = gr.Slider(
                minimum=0.0, maximum=1.0, value=0.8, step=0.05,
                label="🌡️ Temperature (창의성)",
                info="높을수록 창의적·다양, 낮을수록 일관·정확",
            )
            top_p = gr.Slider(
                minimum=0.0, maximum=1.0, value=0.9, step=0.05,
                label="🎲 Top P (다양성)",
                info="어휘 선택 범위 조절",
            )
            max_tokens = gr.Slider(
                minimum=100, maximum=2000, value=1000, step=100,
                label="📝 Max Tokens (답변 길이)",
                info="최대 생성 토큰 수",
            )
            gr.Markdown(
                """
                ---
                **🔢 대화 메모리:** 최근 3쌍
                **🖼️ 지원 이미지:** PNG / JPG / WEBP / GIF
                """
            )

    # ── 이벤트 연결 ────────────────────────────────────────────────────────────
    msg_input.submit(
        user_submit,
        inputs=[msg_input, chatbot, api_history],
        outputs=[chatbot, api_history, msg_input],
    ).then(
        bot_respond,
        inputs=[chatbot, api_history, temperature, top_p, max_tokens],
        outputs=[chatbot, api_history],
    )

    clear_btn.click(lambda: ([], []), outputs=[chatbot, api_history])


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), share=True)
