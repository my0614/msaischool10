import gradio as gr
import cv2

from PIL import Image


def detect_object(image_array, is_bgr=True):
    image_array = image_array.copy()  # read-only 배열 → 쓰기 가능 복사본

    cascade_file_path = (
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    model = cv2.CascadeClassifier(cascade_file_path)

    bounding_boxes = model.detectMultiScale(
        image=image_array,
        scaleFactor=1.05,
        minNeighbors=5,
        minSize=(30, 30),
    )

    for x, y, w, h in bounding_boxes:
        cv2.rectangle(image_array, (x, y), (x + w, y + h), (0, 255, 0), 2)

    if is_bgr:
        image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)

    return image_array


import os

image = cv2.imread("./istockphoto-1480574526-2048x2048.jpg")

result = detect_object(image)

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_20260611_opencv.jpg")
result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
cv2.imwrite(output_path, result_bgr)
print(f"결과 이미지 저장 완료: {output_path}")

with gr.Blocks() as demo:

    def stream_webcam(image_array):
        result_image = detect_object(image_array=image_array, is_bgr=False)
        return result_image

    gr.Markdown("객체 감지 서비스")

    with gr.Row():
        stream_image = gr.Image(
            label="웹캠",
            sources=["webcam"],
            webcam_options=gr.WebcamOptions(mirror=False),
        )
        result_image = gr.Image(label="감지 결과", interactive=False)

    stream_image.stream(
        stream_webcam, inputs=[stream_image], outputs=[result_image]
    )

demo.launch()