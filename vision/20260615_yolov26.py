from ultralytics import YOLO
from PIL import Image, ImageDraw
import gradio as gr
from io import BytesIO
import requests
import cv2

model = YOLO("yolov8n.pt")

url = "https://ultralytics.com/images/bus.jpg"
response = requests.get(url)
image = Image.open(BytesIO(response.content)).convert("RGB")
image_array = cv2.cvtColor(__import__("numpy").array(image), cv2.COLOR_RGB2BGR)


def detect_object(image_array):
    results = model(image_array)
    result = results[0]
    label_list = result.names
    boxes = result.boxes
    class_index_list = boxes.cls.cpu().numpy()
    confidence_list = boxes.conf.cpu().numpy()
    bounding_box_list = boxes.xyxy.cpu().numpy()

    draw = ImageDraw.Draw(image)

    for bounding_box, confidence, label_index in zip(
        bounding_box_list, confidence_list, class_index_list
    ):
        x1, y1, x2, y2 = bounding_box
        label_text = label_list[int(label_index)]
        print(x1, y1, x2, y2, confidence, label_text)

        draw.rectangle([(x1, y1), (x2, y2)], outline=(0, 255, 0), width=2)
        draw.text(
            (x1 + 5, y1 + 5),
            text="{}({:.2f}%)".format(label_text, confidence * 100),
            fill=(0, 255, 0),
        )

    return image


print(detect_object(image_array))

with gr.Blocks() as demo:

    def stream_webcam(image_array):
        result_image = detect_object(image_array)
        return result_image

    with gr.Row():
        webcam_image = gr.Image(
            label="웹캠",
            sources=["webcam"],
            webcam_options=gr.WebcamOptions(mirror=False),
        )
        result_image = gr.Image(label="감지 결과", interactive=False)

    webcam_image.stream(
        stream_webcam, inputs=[webcam_image], outputs=[result_image]
    )

demo.launch()