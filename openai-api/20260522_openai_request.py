import requests
import json

url = "https://10ai003-openai.openai.azure.com/openai/deployments/gpt-4o-mini-10ai003/chat/completions?api-version=2025-01-01-preview"

headers = {
  'Content-Type': 'application/json',
  'api-key': 'REMOVED'
}


def request_openai(message):
  payload = json.dumps({
    "messages": [
      {
        "role": "system",
        "content": [
          {
            "type": "text",
            "text": "사용자가 정보를 찾는 데 도움이 되는 AI 도우미입니다."
          }
        ]
      },
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": message
          }
        ]
      }
    ],
    "temperature": 0.7,
    "top_p": 0.95,
    "max_tokens": 6553
  })
  response = requests.request("POST", url, headers=headers, data=payload)

  if response.status_code == 200:
    result = result['choices'][0]['message']['content']
    return result
  else:
    print("status_code", response.status_code)
    


message = input("원하는 메세지를 입력해주세요!")
print(request_openai(message))

