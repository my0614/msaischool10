import os
from openai import AsyncAzureOpenAI, AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("ENDPOINT_URL")
deployment = os.getenv("DEPLOYMENT_NAME")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")

client = AsyncAzureOpenAI(
    azure_endpoint=endpoint,
    api_key=subscription_key,
    api_version="2025-01-01-preview",
)

# 맛집 추천으로 프롬프트 통일
SYSTEM_PROMPT = "너는 맛집 추천 전문가야. 최소 3가지의 맛집을 이름, 특징과 함께 친절하게 소개해줘."

def my_chatbot(message_cnt=3, temp=0.7, top_p=0.9, stop=None):
    # message_cnt가 확실히 숫자로 계산되도록 보장
    message_limit = int(message_cnt) * 2

    chat_prompt = [
        {
            "role": "system",
            "content": [{"type": "text", "text": SYSTEM_PROMPT}]
        }
    ]

    print("🤖 맛집 추천 챗봇이 시작되었습니다! 대화를 시작하세요. (종료하려면 Ctrl+C)")

    # 함수 내부에 무한 루프 하나만 둡니다.
    while True:
        try:
            user_input = input("\n🙋 유저 입력: ").strip()
            if not user_input:
                continue

            # 1. 대화 내역 갯수 제어 (이전 대화가 너무 많아지면 슬라이싱)
            if len(chat_prompt) > (1 + message_limit):
                chat_prompt = [chat_prompt[0]] + chat_prompt[-message_limit:]

            # 2. 유저 입력 추가
            chat_prompt.append({
                "role": "user",
                "content": [{"type": "text", "text": user_input}]
            })
            
            # 3. Azure OpenAI API 호출
            completion = client.chat.completions.create(
                model=deployment,
                messages=chat_prompt,
                max_tokens=1000, # 6553은 너무 크므로 적당히 조절
                temperature=temp,
                top_p=top_p,
                stop=stop,
                stream=False
            )
            print("completion",completion)
            # 4. 답변 추출 및 출력
            ai_response = completion.choices[0].message.content
            print(f"💬 챗봇 답변:\n{ai_response}")

            # 5. AI 답변을 내역에 추가
            chat_prompt.append({
                "role": "assistant",
                "content": [{"type": "text", "text": ai_response}]
            })

        except KeyboardInterrupt:
            print("\n👋 대화를 종료합니다.")
            break

# 함수 실행 (따로 외부 루프를 돌리지 않고 한 번만 실행하면 내부에서 돕니다)
my_chatbot(message_cnt=3)