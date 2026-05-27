import os
import requests
import json
import base64
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("IMAGE_ENDPOINT_URL")

payload = json.dumps({
  "prompt": "피카소가 그린 형식의 바다 풍경을 그려줘",
  "size": "1024x1024",
  "quality": "low",
  "output_compression": 100,
  "output_format": "png",
  "n": 1
})
headers = {
  'Content-Type': 'application/json',
  'api-key': os.getenv("IMAGE_API_KEY")
}

response = requests.request("POST", url, headers=headers, data=payload)

  # JSON으로 파싱 먼저
result = response.json()

b64_json = result["data"][0]["b64_json"]

# b64_json → bytes → PIL Image
image_bytes = base64.b64decode(b64_json)
image = Image.open(io.BytesIO(image_bytes))

# 파일로 저장
image.save("output.png")