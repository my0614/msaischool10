from azure.cognitiveservices.vision.customvision.training import (
    CustomVisionTrainingClient,
)
from azure.cognitiveservices.vision.customvision.prediction import (
    CustomVisionPredictionClient,
)
from azure.cognitiveservices.vision.customvision.training.models import (
    ImageFileCreateBatch,
    ImageFileCreateEntry,
    Region,
)
from msrest.authentication import ApiKeyCredentials
from PIL import Image, ImageDraw, ImageFont
import platform
import requests
from io import BytesIO
from dotenv import load_dotenv
import os, time, uuid
import json

load_dotenv()

# 환경 변수 설정
TRAIN_ENDPOINT = os.getenv("CUSTOM_VISION_TRAIN_ENDPOINT")
PREDICTION_ENDPOINT = os.getenv("CUSTOM_VISION_PREDICTION_ENDPOINT")
TRAIN_KEY = os.getenv("CUSTOM_VISION_TRAIN_KEY")
PREDICTION_KEY = os.getenv("CUSTOM_VISION_PREDICTION_KEY")
RESOURCE_ID = os.getenv("CUSTOM_VISION_RESOURCE_ID")

def get_font(width):
    font_size = (width / 900) * 15
 
    try:
        if platform.system() == "Windows":
            return ImageFont.truetype("malgun.ttf", font_size)
        elif platform.system() == "Darwin":  # macOS
            return ImageFont.truetype("AppleGothic.ttf", font_size)
        else:  # Linux 등
            return ImageFont.load_default(size=font_size)
    except IOError:
        return ImageFont.load_default()
    
# trainer, predition 객체화
training_credentials = ApiKeyCredentials(in_headers={"Training-key": TRAIN_KEY})
prediction_credentials = ApiKeyCredentials(
    in_headers={"Prediction-key": PREDICTION_KEY}
)

trainer = CustomVisionTrainingClient(
    endpoint=TRAIN_ENDPOINT, credentials=training_credentials
)
predictor = CustomVisionPredictionClient(
    endpoint=PREDICTION_ENDPOINT, credentials=prediction_credentials
)

for domain in trainer.get_domains():
    print("{} | {} | {}".format(domain.name, domain.type, domain.id))

for project in trainer.get_projects():
    print("{} | {} | {}".format(project.name, project.id, project.description))
    
    
project_name = "10ai003-kitchen"
description = "포크와 가위를 탐지하는 모델"

project = None
domain = None

for pro in trainer.get_projects():
    if project_name == pro.name:
        print(f"프로젝트 존재 {pro.id}")
        project = pro
        break
    

for c in trainer.get_domains():
    # General (compact) | ObjectDetection
    if c.type == "ObjectDetection" and c.name == "General (compact)":
        print("도메인을 들고 옵니다. Domain Name : {}".format(c.name))
        domain = c
        break
    
print(project, domain)
if project == None:
    print("프로젝트가 없으므로, 생성하겠습니다")
    trainer.create_project(name=project_name, description=description, domain_id=domain.id)
        
TAG_LIST = ['포크', '가위']

existing_tags = {t.name: t for t in trainer.get_tags(project.id)}

tags_dict = {}
for tag_name in TAG_LIST:
    if tag_name in existing_tags:
        print(f"{tag_name}이 존재해서 가져옴")
        tags_dict[tag_name] = existing_tags[tag_name]
    else:
        print(f"tag 생성: {tag_name}")
        tags_dict[tag_name] = trainer.create_tag(project.id, tag_name)
        
with open("./label.json", "r") as f:
    label_data = json.load(f)

tagged_images = []

for file_name, region in label_data["fork"].items():
    left, top, width, height = region
    with open("../data/fork/{}.jpg".format(file_name), "rb") as image_file:
        image_data = image_file.read()
    regions = [Region(tag_id=tags_dict['포크'].id, left=left, top=top, width=width, height=height)]
    tagged_images.append(ImageFileCreateEntry(name=file_name, contents=image_data, regions=regions))

for file_name, region in label_data["scissors"].items():
    left, top, width, height = region
    with open("../data/scissors/{}.jpg".format(file_name), "rb") as image_file:
        image_data = image_file.read()
    regions = [Region(tag_id=tags_dict['가위'].id, left=left, top=top, width=width, height=height)]
    tagged_images.append(ImageFileCreateEntry(name=file_name, contents=image_data, regions=regions))

upload_result = trainer.create_images_from_files(
    project.id, ImageFileCreateBatch(images=tagged_images)
)

if not upload_result.is_batch_successful:
    print("이미지 업로드 실패")
    for image in upload_result.images:
        print(f"{image.source_url}: {image.status}")
else:
    print(f"이미지 {len(tagged_images)}개 업로드 완료")
    
    
# train
if len(trainer.get_iterations(project.id)) > 0:
    iteration = trainer.get_iterations(project.id)[0]
else:
    iteration = trainer.train_project(project.id)

print(iteration)

while iteration.status == "Training":
    print(iteration.name, iteration.status)
    time.sleep(3)
    iteration = trainer.get_iteration(project.id, iteration.id)

print("학습완료 ->", iteration.name, iteration.status)
    
# 배포
publish_name = "kitchen_v1"
try:
    trainer.publish_iteration(project.id, iteration.id, publish_name, RESOURCE_ID)
except Exception as e:
    print("이미 게시된 모델입니다.", publish_name)
    
# predictor
# with open("../data/fork/fork_1.jpg", "rb") as image_file:
#     image_data = image_file.read()
# response = predictor.detect_image(project.id, publish_name, image_data)

# for prediction in response.predictions:
#     name = prediction.tag_name
#     probability = prediction.probability
#     bounding_box = prediction.bounding_box
#     x = bounding_box.left
#     y = bounding_box.top
#     w = bounding_box.width
#     h = bounding_box.height
#     if probability > 0.5:
#         print("{}({:.2f}%) {} {} {} {}".format(name, probability * 100, x, y, w, h))
image_url = "https://images.unsplash.com/photo-1668853060178-2d53667b7345?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"

response = requests.get(image_url)
image_data = response.content

image = Image.open(BytesIO(image_data))
draw = ImageDraw.Draw(image)

image_width, image_height = image.size
font = get_font(image_width)

response = predictor.detect_image_url(project.id, publish_name, image_url)
# response = predictor.detect_image(project.id, publish_name, image_data)

for prediction in response.predictions:
    name = prediction.tag_name
    probability = prediction.probability
    bounding_box = prediction.bounding_box
    x = bounding_box.left * image_width
    y = bounding_box.top * image_height
    w = bounding_box.width * image_width
    h = bounding_box.height * image_height
    
    if probability > 0.5:
        print("{}({:.2f}%) {} {} {} {}".format(name, probability * 100, x, y, w, h))
        # 결과 값을 통해 이미지에 그려 준다.
        draw.rectangle([(x, y), (x + w, y + h)], outline="red", width=2)
        draw.text(
            (x + 10, y + 10),
            "{}({:.2f}%)".format(name, probability * 100),
            fill="red",
            font=font,
        )

output_path = os.path.join(os.path.dirname(__file__), "result_20260610.jpg")
image.save(output_path)
print(f"결과 이미지 저장 완료: {output_path}")

# model export
from azure.cognitiveservices.vision.customvision.training.models import ExportPlatform

export_list = trainer.get_exports(project.id, iteration.id)

if len(export_list) > 0:
    export = export_list[0]
else:
    export = trainer.export_iteration(project.id, iteration.id, ExportPlatform.onnx)

#print(export.download_uri)

# model download

