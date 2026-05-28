import os
import time
import json
from datetime import datetime, timedelta
from openai import AzureOpenAI
from dotenv import load_dotenv
from pykrx import stock as krx

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("ENDPOINT_URL"),
    api_key=os.getenv("ASSISTANT_KEY"),
    api_version="2024-05-01-preview",
)

STOCK_CODE = {
    "삼성전자": "005930",
    "sk하이닉스": "000660",
    "카카오": "035720",
    "네이버": "035420",
    "lg에너지솔루션": "373220",
    "현대차": "005380",
    "기아": "000270",
}

def get_stock_price(symbol):
    """pykrx로 한국 주식 종가 조회"""
    name_lower = symbol.lower().replace(" ", "")
    code = None
    for key, val in STOCK_CODE.items():
        if key.replace(" ", "") in name_lower:
            code = val
            break
    if not code:
        return json.dumps({"error": f"{symbol}의 종목 코드를 찾을 수 없습니다."})

    today = datetime.today().strftime("%Y%m%d")
    week_ago = (datetime.today() - timedelta(days=7)).strftime("%Y%m%d")
    df = krx.get_market_ohlcv(week_ago, today, code)
    if df.empty:
        return json.dumps({"error": "데이터 없음"})

    row = df.iloc[-1]
    return json.dumps({
        "종목명": symbol,
        "종가": int(row["종가"]),
        "시가": int(row["시가"]),
        "고가": int(row["고가"]),
        "저가": int(row["저가"]),
        "거래량": int(row["거래량"]),
    }, ensure_ascii=False)


# Assistant 생성
assistant = client.beta.assistants.create(
    model="gpt-4o-mini-10ai003",
    instructions="당신은 주식 정보를 제공하는 도우미입니다.",
    tools=[
        {"type": "file_search"},
        {"type": "code_interpreter"},
        {
            "type": "function",
            "function": {
                "name": "get_stock_price",
                "description": "한국 주식 종목의 종가, 시가, 고가, 저가, 거래량을 조회합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "종목명 (예: 삼성전자, 카카오, SK하이닉스)",
                        }
                    },
                    "required": ["symbol"],
                },
            }
        },
    ],
    tool_resources={
        "file_search": {"vector_store_ids": ["vs_KLIufR2vUjiOlAFNfhvhqvx5"]},
        "code_interpreter": {"file_ids": []},
    },
    temperature=1,
    top_p=1,
)

# 스레드 생성 및 질문
thread = client.beta.threads.create()
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="삼성전자랑 카카오 주가 알려줘",
)

# 실행
run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
)

# 완료 또는 함수 호출 대기
while run.status in ["queued", "in_progress", "cancelling"]:
    time.sleep(1)
    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

# requires_action: 함수 호출 처리
if run.status == "requires_action":
    tool_calls = run.required_action.submit_tool_outputs.tool_calls
    tool_outputs = []

    for tool_call in tool_calls:
        args = json.loads(tool_call.function.arguments)
        print(f"함수 호출: {tool_call.function.name}({args})")

        if tool_call.function.name == "get_stock_price":
            result = get_stock_price(args.get("symbol"))
        else:
            result = json.dumps({"error": "Unknown function"})

        print(f"결과: {result}")
        tool_outputs.append({
            "tool_call_id": tool_call.id,
            "output": result,
        })

    # 결과 제출 후 재실행
    run = client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread.id,
        run_id=run.id,
        tool_outputs=tool_outputs,
    )

    # 완료 대기
    while run.status in ["queued", "in_progress", "cancelling"]:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

if run.status == "completed":
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    print("\n=== AI 응답 ===")
    print(messages.data[0].content[0].text.value)
else:
    print(f"오류: {run.status}")
