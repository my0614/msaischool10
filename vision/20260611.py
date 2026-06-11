import onnxruntime
import numpy
import sys
import os
import requests
import platform
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ONNX_MODEL_FILENAME = os.path.join(SCRIPT_DIR, "model.onnx")
LABELS_FILENAME = os.path.join(SCRIPT_DIR, "label.txt")
TEST_IMAGE = "https://cdn.pixabay.com/photo/2014/12/02/14/49/fork-554064_1280.jpg"

sys.path.append(os.path.join(SCRIPT_DIR, "customvision_model", "python"))

from onnxruntime_predict import ONNXRuntimeObjectDetection


def get_font(width):
    font_size = int((width / 900) * 15)
    try:
        if platform.system() == "Windows":
            return ImageFont.truetype("malgun.ttf", font_size)
        elif platform.system() == "Darwin":
            return ImageFont.truetype("AppleGothic.ttf", font_size)
        else:
            return ImageFont.load_default(size=font_size)
    except IOError:
        return ImageFont.load_default()


def random_color():
    import random
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


with open(LABELS_FILENAME, "r", encoding="utf-8") as f:
    labels = [l.strip() for l in f.readlines()]

print("Labels:", labels)

kitchen_model = ONNXRuntimeObjectDetection(ONNX_MODEL_FILENAME, labels)

image_response = requests.get(TEST_IMAGE)
image = Image.open(BytesIO(image_response.content))
draw = ImageDraw.Draw(image)
image_width, image_height = image.size

font = get_font(image_width)
predictions = kitchen_model.predict_image(image)

for prediction in predictions:
    color = random_color()
    tag_name = prediction["tagName"]
    probability = prediction["probability"]
    bounding_box = prediction["boundingBox"]
    x = bounding_box["left"] * image_width
    y = bounding_box["top"] * image_height
    w = bounding_box["width"] * image_width
    h = bounding_box["height"] * image_height

    if x < 0:
        x = 0
    if y < 0:
        y = 0

    if probability < 0.5:
        continue

    print("{} ({:.2f}%) x={:.1f} y={:.1f} w={:.1f} h={:.1f}".format(
        tag_name, probability * 100, x, y, w, h
    ))

    draw.rectangle([(x, y), (x + w, y + h)], outline=color, width=3)
    draw.text(
        (x + 10, y + 10),
        "{} : {:.2f}%".format(tag_name, probability * 100),
        fill=color,
        font=font,
    )

output_path = os.path.join(SCRIPT_DIR, "result_20260611.jpg")
image.save(output_path)
print(f"결과 이미지 저장 완료: {output_path}")
