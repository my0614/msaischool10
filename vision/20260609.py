import os
import gradio as gr
import requests
from dotenv import load_dotenv

load_dotenv()


def request_vision(image_url):
    endpoint = os.getenv("AZURE_VISION_ENDPOINT")

    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("AZURE_VISION_KEY"),
        "Content-Type": "application/json",
    }

    body = {"uri": image_url}

    response = requests.post(
        endpoint,
        headers=headers,
        json=body
    )

    if not response.ok:
        print(f"Error: {response.status_code} - {response.text}")
        return None

    response_json = response.json()

    return response_json


print(request_vision(
    "https://images.unsplash.com/photo-1773332598289-ed0444ad1d6f"
))