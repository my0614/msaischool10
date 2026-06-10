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