import gradio as gr
import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

def request_document_intelligence(image_path):
    endpoint = os.getenv("DI_ENDPOINT")
    header = {"Content-Type":"application/octet-stream","Ocp-Apim-Subscription-Key": os.getenv("DI_API_KEY")}
    body = {}
    with open(image_path, "rb") as image_file:
        body = image_file.read()
    response = requests.post(endpoint, headers=header, data=body)
    operation_location = response.headers.get('operation-location')
    print(operation_location)
    
    while True:
        result_response = requests.get(operation_location, headers={"Ocp-Apim-Subscription-Key":header["Ocp-Apim-Subscription-Key"]})
        
        if not result_response.ok:
            print(result_response.status_code, result_response.reason)
            return None
        
        result_json = result_response.json()
        current_status = result_json.get('status')
        print(current_status)

        if current_status == "running":
            time.sleep(1)
            continue
        else:
            break
        
    return result_json

image_path = "../data/sample.png"
print(request_document_intelligence(image_path))
