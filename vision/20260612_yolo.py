import cv2
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

weights_path = "./yolo/yolov3.weights"
coco_path = "./yolo/coco.names"
config_path = "./yolo/yolov3.cfg"

coco_path = "yolo/coco.names"
  
with open(coco_path, "r", encoding="utf-8") as coco_file:
      label_list = coco_file.read().strip().split("\n")
net = cv2.dnn.readNet(weights_path, config_path)
image_array = cv2.imread("response_content.jpg")

image = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
draw = ImageDraw.Draw(image)

image_width, image_height = image.size

blob = cv2.dnn.blobFromImage(
    image_array, 1 / 255.0, (416, 416), swapRB=True, crop=False
)

net.setInput(blob)

layer_name_list = net.getLayerNames()
out_layer_list = net.getUnconnectedOutLayersNames()

prediction_list = net.forward("yolo_82")

for prediction in prediction_list:
    bounding_box = prediction[:4] * np.array(
        [image_width, image_height, image_width, image_height]
    )
    center_x, center_y, w, h = bounding_box
    score_list = prediction[5:]
    
    x = int(center_x - w / 2)
    y = int(center_y - h / 2)
    
    label_index = np.argmax(score_list)
    if score_list[label_index] > 0:
        draw.rectangle([(x, y), (x + w, y + h)], outline="red", width=2)
        # print(score_list[label_index], label_index, label_list[label_index])

image.save("./result_20260612.jpg")
print(f"결과 이미지 저장 완료")
