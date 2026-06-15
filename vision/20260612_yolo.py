import cv2
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import platform
import gradio as gr
import requests
import base64
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv("../.env")

weights_path = "./yolo/yolov3.weights"
coco_path = "./yolo/coco.names"
config_path = "./yolo/yolov3.cfg"

coco_path = "yolo/coco.names"
  

def get_font(width):
    font_size = max(12, int((width / 900) * 15))
    try:
        if platform.system() == "Windows":
            return ImageFont.truetype("malgun.ttf", font_size)
        elif platform.system() == "Darwin":
            for path in [
                "/Library/Fonts/AppleGothic.ttf",
                "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
                "/System/Library/Fonts/AppleGothic.ttf",
            ]:
                try:
                    return ImageFont.truetype(path, font_size)
                except IOError:
                    continue
        try:
            return ImageFont.load_default(size=font_size)
        except TypeError:
            return ImageFont.load_default()
    except IOError:
        return ImageFont.load_default()


with open(coco_path, "r", encoding="utf-8") as coco_file:
      label_list = coco_file.read().strip().split("\n")
net = cv2.dnn.readNet(weights_path, config_path)
image_array = cv2.imread("response_content.jpg")

image = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
draw = ImageDraw.Draw(image)

image_width, image_height = image.size
font = get_font(image_width)

blob = cv2.dnn.blobFromImage(
    image_array, 1 / 255.0, (416, 416), swapRB=True, crop=False
)

net.setInput(blob)

layer_name_list = net.getLayerNames()
out_layer_list = net.getUnconnectedOutLayersNames()

detection_list = net.forward(out_layer_list)
bounding_box_list = list()
confidence_list = list()
label_text_list = list()
color_list = list()

for prediction_list, color in zip(detection_list, ["yellow", "aqua", "springgreen"]):
    for prediction in prediction_list:
        bounding_box = prediction[:4] * np.array(
            [image_width, image_height, image_width, image_height]
        )
        center_x, center_y, w, h = bounding_box
        score_list = prediction[5:]

        max_score = float(np.max(score_list))
        max_index = int(np.argmax(score_list))

        if max_score > 0.5:
            x = int(center_x - w / 2)
            y = int(center_y - h / 2)
            bounding_box_list.append([x, y, int(w), int(h)])
            confidence_list.append(max_score)
            label_text_list.append(label_list[max_index])
            color_list.append(color)

extracted_index_list = cv2.dnn.NMSBoxes(bounding_box_list, confidence_list, 0.5, 0.5)


for extracted_index in extracted_index_list:

    bounding_box = bounding_box_list[extracted_index]
    x, y, w, h = bounding_box

    confidence = confidence_list[extracted_index]
    text = label_text_list[extracted_index]
    color = color_list[extracted_index]

    draw.rectangle([(x, y), (x + w, y + h)], outline=color, width=2)
    draw.text(
        (x + 5, y + 5),
        "{}({:.2f}%)".format(text, confidence * 100),
        fill=color,
        font=font,
    )

# image.save("./result_20260612.jpg")
# print(f"결과 이미지 저장 완료")

def detect_objects(image_array):

    image_array = image_array.copy()
    image = Image.fromarray(image_array)
    draw = ImageDraw.Draw(image)

    image_width, image_height = image.size

    font = get_font(image_width)

    blob = cv2.dnn.blobFromImage(
        image_array, 1 / 255.0, (416, 416), swapRB=True, crop=False
    )

    net.setInput(blob)

    layer_name_list = net.getLayerNames()
    out_layer_list = net.getUnconnectedOutLayersNames()

    detection_list = net.forward(out_layer_list)

    bounding_box_list = list()
    confidence_list = list()
    label_text_list = list()
    color_list = list()

    for prediction_list, color in zip(
        detection_list, ["yellow", "aqua", "springgreen"]
    ):
        for prediction in prediction_list:
            bounding_box = prediction[:4] * np.array(
                [image_width, image_height, image_width, image_height]
            )
            center_x, center_y, w, h = bounding_box
            score_list = prediction[5:]

            max_score = float(np.max(score_list))
            max_index = int(np.argmax(score_list))

            if max_score > 0.5:
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                bounding_box_list.append([x, y, int(w), int(h)])
                confidence_list.append(max_score)
                label_text_list.append(label_list[max_index])
                color_list.append(color)

    extracted_index_list = cv2.dnn.NMSBoxes(bounding_box_list, confidence_list, 0.5, 0.5)

    for extracted_index in extracted_index_list:
        bounding_box = bounding_box_list[extracted_index]
        x, y, w, h = bounding_box

        confidence = confidence_list[extracted_index]
        text = label_text_list[extracted_index]
        color = color_list[extracted_index]

        draw.rectangle([(x, y), (x + w, y + h)], outline=color, width=2)
        draw.text(
            (x + 5, y + 5),
            "{}({:.2f}%)".format(text, confidence * 100),
            fill=color,
            font=font,
        )

    return image

import requests


def request_tts(text):
    endpoint = "https://eastus.tts.speech.microsoft.com/cognitiveservices/v1"
    # POST
    headers = {
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "riff-8khz-16bit-mono-pcm",
        "Ocp-Apim-Subscription-Key": os.getenv("AZURE_SPEECH_KEY"),
    }

    body = f"""
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
xmlns:mstts="http://www.w3.org/2001/10/synthesis" xml:lang="ko-KR">
    <voice name="ko-KR-SunHi:DragonHDLatestNeural">
        {text}
    </voice>
</speak>
"""

    response = requests.post(endpoint, headers=headers, data=body)

    if response.status_code != 200:
        print(f"TTS Error: {response.status_code} - {response.text}")
        return None

    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = "output_{}.wav".format(now)

    with open(file_name, "wb") as audio_file:
        audio_file.write(response.content)

    return file_name


def request_gpt(image_array):
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    headers = {
        "Authorization": "Bearer {}".format(os.environ["AZURE_OPENAI_API_KEY"])
    }
    
    success, encoded_image = cv2.imencode(".jpg", image_array)

    if not success:
        raise ValueError("이미지 인코딩에 실패했습니다.")

    base64_string = base64.b64encode(encoded_image).decode("utf-8")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    body = {
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "CCTV 화면에서 감지된 객체명과 확률을 아래 형식으로 출력합니다.\n"
                            "Detected Object(s): 객체명1 (확률1%), 객체명2 (확률2%), ...\n"
                            "객체가 없으면 No objects detected. 로 표기합니다."
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "이 CCTV 화면에서 감지된 물체와 각각의 확률을 알려줘",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "[2023-10-01 13:45:23] Detected Object(s): Cat (93%), Dog (87%)",
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "이 CCTV 화면에서 감지된 물체와 각각의 확률을 알려줘",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "[2023-10-01 14:15:53] Detected Object(s): Bicycle (99%)",
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/jpeg;base64,{}".format(base64_string)
                        },
                    },
                    {
                        "type": "text",
                        "text": "현재 시각은 {}입니다. 이 CCTV 화면에서 감지된 물체와 각각의 확률을 알려줘".format(now),
                    },
                ],
            },
        ],
        "max_completion_tokens": 800,
        "temperature": 0.7,
        "top_p": 0.95,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }

    try:
        response = requests.post(endpoint, headers=headers, json=body, timeout=30)
    except requests.exceptions.ReadTimeout:
        print("Error: 요청 시간 초과")
        return None

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return None

    response_json = response.json()
    content = response_json["choices"][0]["message"]["content"]
    return content

with gr.Blocks() as demo:

    def stream_webcam(image_array):
        result_image = detect_objects(image_array)
        return result_image

    def click_capture(image):
        return image

    def change_capture(image_array, histories):
        content = request_gpt(image_array)
        label_text = datetime.datetime.now().strftime("%Y년%m월%d일 %H:%M:%S")
        histories.append(
            {
                "role": "user",
                "content": gr.Image(label=label_text, value=image_array),
            }
        )
        histories.append({"role": "assistant", "content": content})
        if content is None:
            return histories, None
        audio_file_name = request_tts(content)
        return histories, audio_file_name

    with gr.Row():
        stream_image = gr.Image(
            label="웹캠",
            sources=["webcam"],
            webcam_options=gr.WebcamOptions(mirror=False),
        )
        result_image = gr.Image(label="감지 결과", interactive=False, type="pil")
        capture_image = gr.Image(label="이상 징후 발생", interactive=False)

    capture_button = gr.Button("이상 징후 발생")

    chatbot = gr.Chatbot(label="분석 결과")
    tts_audio = gr.Audio(label="분석 결과", interactive=False, autoplay=True)

    stream_image.stream(stream_webcam, inputs=[stream_image], outputs=[result_image])
    capture_button.click(click_capture, inputs=[result_image], outputs=[capture_image])
    capture_image.change(
        change_capture, inputs=[capture_image, chatbot], outputs=[chatbot, tts_audio]
    )

demo.launch()