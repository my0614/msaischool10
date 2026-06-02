import gradio as gr
import requests
import os
from dotenv import load_dotenv
import time
from PIL import Image, ImageDraw, ImageFont
import random
import platform

load_dotenv()

def random_color():
  return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


def get_font(width):
    font_size = (width / 900) * 15 
    
    try:
        if platform.system() == "Windows":
            # 윈도우: 맑은 고딕
            return ImageFont.truetype("malgun.ttf", font_size)
        elif platform.system() == "Darwin":  # macOS
            # 맥: 애플 고딕
            return ImageFont.truetype("AppleGothic.ttf", font_size)
        else:  # Linux 등
            # 기본 폰트 (한글 지원 안 될 수 있음)
            return ImageFont.load_default(size=font_size)
    except IOError:
        # 지정한 폰트 파일이 없을 경우 PIL 기본 폰트 사용
        return ImageFont.load_default()
    
def request_document_intelligence(image_path):
    endpoint = os.getenv("DI_ENDPOINT")
    header = {"Content-Type":"application/octet-stream","Ocp-Apim-Subscription-Key": os.getenv("DI_API_KEY")}
    body = {}
    with open(image_path, "rb") as image_file:
        body = image_file.read()
    response = requests.post(endpoint, headers=header, data=body)
    operation_location = response.headers.get('operation-location')
    print(operation_location)
    
    while True:
        result_response = requests.get(operation_location, headers={"Ocp-Apim-Subscription-Key":header["Ocp-Apim-Subscription-Key"]})
        
        if not result_response.ok:
            print(result_response.status_code, result_response.reason)
            return None
        
        result_json = result_response.json()
        current_status = result_json.get('status')
        print(current_status)

        if current_status == "running":
            time.sleep(1)
            continue
        else:
            break
        
    return result_json

def draw_image(image_path, result_json):
    print("draw image")
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    
    block_list = result_json.get("analyzeResult").get("paragraphs")

    for block in block_list:
        content = block.get("content", "")
        polygon = block.get("boundingRegions")[0].get("polygon")
        format_pol = []
        for i in range(0, len(polygon), 2):
            format_pol.append((polygon[i], polygon[i + 1]))
        draw.polygon(format_pol, outline="red", width=2)
        draw.text((format_pol[0][0],format_pol[0][1]), content, fill=random_color(), font=get_font(900))

    output_path = "./result.png"
    image.save(output_path)
    print(f"저장 완료: {output_path}")

    return image


image_path = "../data/sample.png"
result_json =  request_document_intelligence(image_path)
draw_image(image_path, result_json)

with gr.Blocks() as demo:
    sample_text = gr.State("Sample Text")

    def click_send(image_path):
        result_json = request_document_intelligence(image_path)
        image = draw_image(image_path, result_json)
        return image

    with gr.Row():

        input_image = gr.Image(label="Input Image", type="filepath")
        output_image = gr.Image(label="Output Image", type="pil")

    send_button = gr.Button("전송")

    send_button.click(
        click_send,
        inputs=[input_image],
        outputs=[output_image]
    )

demo.launch()