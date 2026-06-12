import cv2
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import platform
import gradio as gr

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

image.save("./result_20260612.jpg")
print(f"결과 이미지 저장 완료")

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


with gr.Blocks() as demo:

    def stream_webcam(image_array):
        result_image = detect_objects(image_array)
        return result_image


    def click_capture(image):
        return image


    def change_capture(image):
        print("CHANGE_CAPTURE")
        pass


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

    capture_image.change(change_capture, inputs=[capture_image], outputs=[])

demo.launch()