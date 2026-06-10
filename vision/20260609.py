import os
import gradio as gr
import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import platform
from urllib.parse import urlparse, urlunparse

load_dotenv()

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
    
def request_vision(image_url, features):
    raw_endpoint = os.getenv("AZURE_VISION_ENDPOINT")
    parsed = urlparse(raw_endpoint)
    endpoint = urlunparse(parsed._replace(query=''))

    params = {"api-version": "2023-10-01", "features": ",".join(features)}
    
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("AZURE_VISION_KEY"),
        "Content-Type": "application/json",
    }

    body = {"uri": image_url}

    response = requests.post(
        endpoint,
        headers=headers,
        params=params,
        json=body
    )

    if not response.ok:
        print(f"Error: {response.status_code} - {response.text}")
        return None

    response_json = response.json()

    return response_json

def draw_image(image_url, data):
    DRAW_LIST = ['objectsResult', 'denseCaptionsResult', 'smartCropsResult']
    COLOR_MAP = {'objectsResult': 'yellow', 'denseCaptionsResult': 'aqua', 'smartCropsResult': 'springgreen'}
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    draw = ImageDraw.Draw(image)
    font = get_font(image.width)

    for feature_key in DRAW_LIST:
        result = data.get(feature_key, None)

        if result is None:
            continue

        block_list = result.get('values', [])
        color = COLOR_MAP.get(feature_key)
        for block_box in block_list:
            box = block_box.get('boundingBox')
            if feature_key == 'objectsResult':
                label = block_box.get('tags', [{}])[0].get('name', '')
                conf = block_box.get('tags', [{}])[0].get('confidence', 0)
                text = "{} {:.0f}%".format(label, conf * 100)
            elif feature_key == 'denseCaptionsResult':
                text = block_box.get('text', '')[:20]
            else:
                text = "crop {}".format(block_box.get('aspectRatio', ''))
            draw.rectangle([(box['x'], box['y']), (box['x']+box['w'], box['y']+box['h'])], outline=color, width=2)
            text = ""

            if "objectsResult" == feature_key:
                tag = block_box.get("tags")[0]
                name = tag["name"]
                confidence = tag["confidence"]
                text = "{}({:.2f}%)".format(name, confidence * 100)

            elif "denseCaptionsResult" == feature_key:
                caption_text = block_box["text"]
                confidence = block_box["confidence"]
                text = "{}({:.2f}%)".format(caption_text, confidence * 100)

            elif "smartCropsResult" == feature_key:
                ratio = block_box["aspectRatio"]
                text = "smartCrops : {:.2f}".format(ratio)

            draw.text((box['x']+5, box['y']+5), text, fill=color, font=font)

    return image

with gr.Blocks() as demo:

    FEATURE_LIST = ["objects", "caption", "denseCaptions", "tags", "smartCrops"]

    def change_features(checked_list):
        print("change", checked_list)
        
        is_show_gender = False
        is_show_smart_crops = False
        
        if "caption" in checked_list or "denseCaptions" in checked_list:
            is_show_gender = True
            
        if "smartCrops" in checked_list:
            is_show_smart_crops = True
            
        return gr.update(visible=is_show_gender), gr.update(visible=is_show_smart_crops)

    def click_send(image_url, features):
        response_json = request_vision(image_url, features)
        result_image = draw_image(image_url, response_json)
        return result_image, response_json

    with gr.Column():
        features_checkbox = gr.CheckboxGroup(
            label="기능 선택",
            choices=FEATURE_LIST,
            value=["objects", "caption", "denseCaptions", "tags", "smartCrops"],
        )
        
        gender_radio = gr.Radio(
            label="성별 중립 옵션",
            choices=[("중립", True), ("구분", False)],
            value=False,
            interactive=True,
        )
        
        smart_crops_text = gr.Textbox(
            label="smartCrops 크기", placeholder="ex) 0.75,1.8", interactive=True
        )
        
        image_url_text = gr.Textbox(
            label="이미지 경로",
            value="https://images.unsplash.com/photo-1773332598289-ed0444ad1d6f",
        )
        
        send_button = gr.Button("전송")
        
        with gr.Row():
            output_image = gr.Image(label="결과 이미지", interactive=False, type="pil")
            output_json = gr.JSON(label="결과 JSON")
            
        send_button.click(
            click_send,
            inputs=[image_url_text, features_checkbox],
            outputs=[output_image, output_json],
        )
        
        features_checkbox.change(
            change_features,
            inputs=[features_checkbox],
            outputs=[gender_radio, smart_crops_text],
        )
demo.launch()