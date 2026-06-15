from ultralytics import YOLO
import cv2

model = YOLO("yolo26n.pt")


image_array = cv2.imread("https://ultralytics.com/images/bus.jpg")
results = model(image_array)

result = results[0]

label_list = result.names
boxes = result.boxes
class_index_list = boxes.cls.cpu().numpy()
confidence_list = boxes.conf.cpu().numpy()
bounding_box_list = boxes.xyxy.cpu().numpy()

print(class_index_list)
print(confidence_list)
print(bounding_box_list)