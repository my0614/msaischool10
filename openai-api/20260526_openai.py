import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI

# 전역 설정
printFullResponse = False
num_tasks = 3

async def call_openai_model(system_message, user_message, model, client):
    # Message 포매팅
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

    print(f"\n[요청 송신] 모델({model})로 요청을 보냅니다... (메시지 길이: {len(user_message)}자)")

    # 모델에 요청 송부
    response = await client.chat.completions.create(
        model=model,
        temperature=0.7,
        max_tokens=800,
        messages=messages
    )

    # 생성된 텍스트 추출
    generated_text = response.choices[0].message.content

    if printFullResponse:
        print("Full response object:")
        print(response)

    return generated_text

async def main():
    try:
        # Azure OpenAI 설정 및 환경 변수 로드
        load_dotenv()

        endpoint = os.getenv("ENDPOINT_URL")
        deployment = os.getenv("DEPLOYMENT_NAME")
        subscription_key = os.getenv("AZURE_OPENAI_API_KEY")

        # 필수 환경 변수 체크
        if not all([endpoint, deployment, subscription_key]):
            print("⚠️ 경고: .env 파일에서 환경 변수를 읽어오지 못했습니다. 변수명을 확인해 주세요.")
            return

        # Azure OpenAI client 설정
        client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=subscription_key,
            api_version="2025-01-01-preview"
        )

        while True:
            # 사용자의 system prompt 수정 또는 확인을 위한 대기
            print("\n" + "="*40)
            print("system.txt 파일을 수정했다면 Enter를 눌러주세요.")
            print("="*40)
            input()

            # 파일 읽기 에러 방지를 위한 예외 처리 내포
            try:
                system_text = open(file="system.txt", encoding="utf-8").read().strip()
                ground_text = open(file="grounding.txt", encoding="utf-8").read().strip()
            except FileNotFoundError as e:
                print(f"❌ 파일 읽기 실패: {e.filename} 파일이 현재 스크립트와 같은 경로에 없습니다.")
                break

            user_text = input("Enter user message, or 'quit' to exit: ")
            if user_text.lower() == 'quit' or system_text.lower() == 'quit':
                print('Exiting program...')
                break

            # Ground content와 사용자 prompt 결합
            full_user_text = user_text + "\n\n[Grounding Context]\n" + ground_text

            # 동시에 여러 요청(task) 생성
            tasks = []
            for i in range(num_tasks):
                task_text = full_user_text + f"\n(Request {i+1})"
                
                task = asyncio.create_task(
                    call_openai_model(
                        system_message=system_text,
                        user_message=task_text,
                        model=deployment, 
                        client=client
                    )
                )
                tasks.append(task)

            print(f"\n🚀 {num_tasks}개의 비동기 요청을 동시에 발송했습니다. 먼저 완료되는 순서대로 출력합니다.")

            # 응답이 도착하는 순서대로 처리
            for completed in asyncio.as_completed(tasks):
                result = await completed
                print(completed)
                print("\n✨ [Processed answer]:")
                print(result)
                print("-" * 30)

    except Exception as ex:
        print(f"Error occurred: {ex}")

# 일반 파이썬 스크립트 실행을 위한 진입점 설정
if __name__ == '__main__':
    asyncio.run(main())