import os
import gradio as gr
import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw
from io import BytesIO

load_dotenv()


def request_vision(image_url):
    endpoint = os.getenv("AZURE_VISION_ENDPOINT")

    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("AZURE_VISION_KEY"),
        "Content-Type": "application/json",
    }

    body = {"uri": image_url}

    response = requests.post(
        endpoint,
        headers=headers,
        json=body
    )

    if not response.ok:
        print(f"Error: {response.status_code} - {response.text}")
        return None

    response_json = response.json()

    return response_json

def draw_image(image_url, data):
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    draw = ImageDraw.Draw(image)

    draw.rectangle([(100, 100), (200, 400)], outline="red", width=2)

    block_list = data.get('objectsResult').get('values')
    for block_box in block_list:
        box = block_box.get('boundingBox')
        name = block_box.get('tags')[0]['name']
        conf = block_box.get('tags')[0]['confidence']
        draw.rectangle([(box['x'], box['y']), (box['x']+box['w'], box['y']+box['h'])], outline="red", width=2)
        draw.text((box['x'], box['y']), "{}{:.2f}%".format(name, conf*100))
        
    return image


with gr.Blocks() as demo:

    def click_send(image_url):
        response_json = request_vision(image_url)
        result_image = draw_image(image_url, response_json)
        return response_json, result_image

    image_url_text = gr.Textbox(
        label="이미지 경로",
        value="https://images.unsplash.com/photo-1773332598289-ed0444ad1d6f",
    )
    send_button = gr.Button("전송")

    with gr.Row():
        output_image = gr.Image(label="결과 이미지", interactive=False, type="pil")
        output_json = gr.JSON(label="결과 JSON")

    send_button.click(
        click_send, inputs=[image_url_text], outputs=[output_json, output_image]
    )

demo.launch()