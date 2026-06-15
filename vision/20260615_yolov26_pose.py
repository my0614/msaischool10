from ultralytics import YOLO
from PIL import Image, ImageDraw
import gradio as gr

model = YOLO("yolov8n-pose.pt")

CONNECTIONS = [
    (5, 7),
    (7, 9),
    (6, 8),
    (8, 10),
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),
]


def detect_object(image_array):
    image = Image.fromarray(image_array.copy())
    draw = ImageDraw.Draw(image)

    results = model(image_array)
    result = results[0]
    xy_list = result.keypoints.xy.cpu().numpy()
    confidence_list = result.keypoints.conf.cpu().numpy()

    for person_keypoints, keypoint_confidences in zip(xy_list, confidence_list):
        for index1, index2 in CONNECTIONS:
            x1, y1 = person_keypoints[index1]
            x2, y2 = person_keypoints[index2]
            draw.line([(x1, y1), (x2, y2)], fill=(0, 0, 255), width=5)

        for point, confidence in zip(person_keypoints, keypoint_confidences):
            x, y = point
            draw.ellipse(
                [(x - 5, y - 5), (x + 5, y + 5)],
                fill=(0, 255, 0),
                outline=(255, 255, 255),
                width=1,
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
