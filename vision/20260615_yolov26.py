from ultralytics import YOLO
from PIL import Image, ImageDraw
import gradio as gr

model = YOLO("yolov8n.pt")


def detect_object(image_array):
    image = Image.fromarray(image_array.copy())
    draw = ImageDraw.Draw(image)

    results = model(image_array)
    result = results[0]
    label_list = result.names
    boxes = result.boxes
    class_index_list = boxes.cls.cpu().numpy()
    confidence_list = boxes.conf.cpu().numpy()
    bounding_box_list = boxes.xyxy.cpu().numpy()

    for bounding_box, confidence, label_index in zip(
        bounding_box_list, confidence_list, class_index_list
    ):
        x1, y1, x2, y2 = bounding_box
        label_text = label_list[int(label_index)]

        draw.rectangle([(x1, y1), (x2, y2)], outline=(0, 255, 0), width=2)
        draw.text(
            (x1 + 5, y1 + 5),
            text="{}({:.2f}%)".format(label_text, confidence * 100),
            fill=(0, 255, 0),
        )

    return image


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
