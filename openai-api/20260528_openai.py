import os
import time
import tempfile
import gradio as gr
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("ENDPOINT_URL"),
    api_key=os.getenv("ASSISTANT_KEY"),
    api_version="2024-05-01-preview",
)

DEPLOYMENT     = "gpt-4o-mini-10ai003"
VECTOR_STORE_ID = "vs_KLIufR2vUjiOlAFNfhvhqvx5"  # 기존에 업로드된 PDF 벡터스토어

assistant = client.beta.assistants.create(
    model=DEPLOYMENT,
    instructions="당신은 문서 요약 전문가입니다. 업로드된 파일을 분석하고 핵심 내용을 명확하게 요약해주세요. 그래프나 데이터가 있으면 시각화도 해주세요.",
    tools=[{"type": "file_search"}, {"type": "code_interpreter"}],
    tool_resources={
        "file_search": {"vector_store_ids": [VECTOR_STORE_ID]},
        "code_interpreter": {"file_ids": []},
    },
    temperature=0.7,
    top_p=1,
)


def run_assistant(user_prompt: str, file_path: str = None, original_name: str = None):
    uploaded_id = None

    # 1. 파일이 있으면 업로드
    if file_path:
        with open(file_path, "rb") as f:
            uploaded = client.files.create(
                file=(original_name, f),
                purpose="assistants",
            )
        uploaded_id = uploaded.id
        attachments = [{
            "file_id": uploaded_id,
            "tools": [{"type": "file_search"}, {"type": "code_interpreter"}],
        }]
    else:
        attachments = []

    # 2. 스레드 생성 + 메시지 추가
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_prompt,
        attachments=attachments,
    )

    # 3. 실행
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    # 4. 완료 대기
    while run.status in ["queued", "in_progress", "cancelling"]:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    if run.status != "completed":
        return f"오류: {run.status}", None

    # 5. 결과 파싱
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    text_result = ""
    image_result = None

    for block in messages.data[0].content:
        if block.type == "text":
            text = block.text.value
            for ann in block.text.annotations:
                text = text.replace(ann.text, "")
            text_result += text.strip()
        elif block.type == "image_file":
            image_data = client.files.content(block.image_file.file_id)
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.write(image_data.content)
            tmp.close()
            image_result = tmp.name

    # 업로드한 파일 정리
    if uploaded_id:
        client.files.delete(uploaded_id)

    return text_result, image_result


def process(file, prompt):
    if not prompt.strip():
        return "질문을 입력해주세요.", None

    if file is not None:
        original_name = os.path.basename(file.name if hasattr(file, "name") else file)
        file_path = file.name if hasattr(file, "name") else file
        return run_assistant(prompt, file_path=file_path, original_name=original_name)
    else:
        # 파일 없이 벡터스토어만으로 답변
        return run_assistant(prompt)


with gr.Blocks(title="파일 요약기") as demo:
    gr.Markdown("## 파일 요약기")
    gr.Markdown("질문만 입력하거나, 파일을 업로드해서 분석을 요청할 수 있습니다. (마지 여행사 PDF 기본 탑재)")

    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(
                label="파일 업로드",
                file_types=[".pdf", ".txt", ".docx", ".csv", ".xlsx", ".py", ".md"],
                file_count="single",
            )
            prompt_input = gr.Textbox(
                label="질문 입력",
                placeholder="예) 두바이 여행 일정 추천해줘 / 업로드한 파일 요약해줘",
                lines=3,
            )
            submit_btn = gr.Button("요약 시작", variant="primary")

        with gr.Column(scale=2):
            text_output = gr.Textbox(label="요약 결과", lines=15)
            image_output = gr.Image(label="생성된 그래프", visible=True)

    submit_btn.click(
        fn=process,
        inputs=[file_input, prompt_input],
        outputs=[text_output, image_output],
    )

    gr.Examples(
        examples=[
            [None, "핵심 내용을 3줄로 요약해줘"],
            [None, "데이터를 분석하고 그래프로 시각화해줘"],
            [None, "주요 키워드와 결론을 뽑아줘"],
        ],
        inputs=[file_input, prompt_input],
    )

if __name__ == "__main__":
    demo.launch(share=True)
