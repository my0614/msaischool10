import os
import json
from openai import AzureOpenAI
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from pykrx import stock as krx

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("ENDPOINT_URL"),
    api_key=os.getenv("ASSISTANT_KEY"),
    api_version="2024-05-01-preview",
)

deployment_name = os.getenv("DEPLOYMENT_NAME")

STOCK_CODE = {
    "삼성전자": "005930",
    "sk하이닉스": "000660",
    "카카오": "035720",
    "네이버": "035420",
    "lg에너지솔루션": "373220",
    "현대차": "005380",
    "기아": "000270",
}

def get_stock_price(name):
    """한국 주식 종목명으로 전날 종가 조회"""
    name_lower = name.lower().replace(" ", "")
    code = None
    for key, val in STOCK_CODE.items():
        if key.replace(" ", "") in name_lower:
            code = val
            break
    if not code:
        return json.dumps({"error": f"{name}의 종목 코드를 찾을 수 없습니다."})

    from datetime import timedelta
    today = datetime.today().strftime("%Y%m%d")
    week_ago = (datetime.today() - timedelta(days=7)).strftime("%Y%m%d")
    df = krx.get_market_ohlcv(week_ago, today, code)
    if df.empty:
        return json.dumps({"error": "데이터 없음"})

    row = df.iloc[-1]
    return json.dumps({
        "종목명": name,
        "종목코드": code,
        "종가": int(row["종가"]),
        "시가": int(row["시가"]),
        "고가": int(row["고가"]),
        "저가": int(row["저가"]),
        "거래량": int(row["거래량"]),
        "기준일": today,
    }, ensure_ascii=False)

def run_conversation():
    # Initial user message
    messages = [{"role": "user", "content": "sk하이닉스 주가 알려줘"}]

    # Define the function for the model
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_multi_data",
                "description": "숫자 2개를 작성해주시면 곱한 결과를 출력해드립니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "num1": {"type": "string", "description": "number 1"},
                        "num2": {"type": "string", "description": "number 2"},
                    },
                    "required": ["num1", "num2"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_stock_price",
                "description": "한국 주식 종목의 전날 종가, 시가, 고가, 저가, 거래량을 조회합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "종목명 (예: 삼성전자, 카카오, SK하이닉스)",
                        },
                    },
                    "required": ["name"],
                },
            }
        },
    ]

    # First API call: Ask the model to use the function
    response = client.chat.completions.create(
        model=deployment_name,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    # Process the model's response
    response_message = response.choices[0].message
    messages.append(response_message)

    print("Model's response:")  
    print(response_message)  

    # Handle function calls
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            function_args = json.loads(tool_call.function.arguments)
            print(f"Function arguments: {function_args}")
            if tool_call.function.name == "get_multi_data":
                result_response = get_multi_data(
                    num1=function_args.get("num1"),
                    num2=function_args.get("num2"),
                )
            elif tool_call.function.name == "get_stock_price":
                result_response = get_stock_price(
                    name=function_args.get("name")
                )
            else:
                result_response = json.dumps({"error": "Unknown function"})
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_call.function.name,
                "content": result_response,
            })
    else:
        print("No tool calls were made by the model.")  

    # Second API call: Get the final response from the model
    final_response = client.chat.completions.create(
        model=deployment_name,
        messages=messages,
    )

    return final_response.choices[0].message.content

# Run the conversation and print the result
print(run_conversation())