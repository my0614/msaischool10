import gradio as gr
import cv2

from PIL import Image


def detect_object(image_array):
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

    image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)

    return image_array


import os

image = cv2.imread("./istockphoto-1480574526-2048x2048.jpg")

result = detect_object(image)

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_20260611_opencv.jpg")
result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
cv2.imwrite(output_path, result_bgr)
print(f"결과 이미지 저장 완료: {output_path}")