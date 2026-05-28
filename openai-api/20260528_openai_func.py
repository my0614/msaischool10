import os
import json
import gradio as gr
from openai import AzureOpenAI
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pykrx import stock as krx
import warnings

warnings.filterwarnings('ignore')
 
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

TOOLS = [
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
        },
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
        },
    },
]


def get_multi_data(num1, num2):
    try:
        result = float(num1) * float(num2)
        return json.dumps({"num1": num1, "num2": num2, "result": result})
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_stock_price(name):
    name_lower = name.lower().replace(" ", "")
    code = None
    for key, val in STOCK_CODE.items():
        if key.replace(" ", "") in name_lower:
            code = val
            break
    if not code:
        return json.dumps({"error": f"{name}의 종목 코드를 찾을 수 없습니다."})

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


def call_tool(tool_name, args):
    if tool_name == "get_multi_data":
        return get_multi_data(args.get("num1"), args.get("num2"))
    elif tool_name == "get_stock_price":
        return get_stock_price(args.get("name"))
    return json.dumps({"error": "Unknown function"})


def chat(user_message, history):
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    # 1차 API 호출
    response = client.chat.completions.create(
        model=deployment_name,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )
    response_message = response.choices[0].message
    messages.append(response_message)

    # 함수 호출 처리
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            result = call_tool(tool_call.function.name, args)
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_call.function.name,
                "content": result,
            })

        # 2차 API 호출 (함수 결과 반영)
        final_response = client.chat.completions.create(
            model=deployment_name,
            messages=messages,
        )
        return final_response.choices[0].message.content

    return response_message.content


with gr.Blocks(title="주식 & 계산 챗봇") as demo:
    gr.Markdown("# 📈 주식 & 계산 챗봇\n지원 종목: 삼성전자, SK하이닉스, 카카오, 네이버, LG에너지솔루션, 현대차, 기아")
    gr.ChatInterface(
        fn=chat,
        examples=[
            "삼성전자 주가 알려줘",
            "SK하이닉스 주가 얼마야?",
            "카카오랑 네이버 주가 비교해줘",
            "35 곱하기 48 계산해줘",
        ],
        chatbot=gr.Chatbot(height=450),
        textbox=gr.Textbox(placeholder="질문을 입력하세요...", container=False, scale=7),
    )

demo.launch(share=True)
