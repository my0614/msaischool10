
import os
import base64
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("ENDPOINT_URL")
deployment = os.getenv("DEPLOYMENT_NAME")
search_endpoint = os.getenv("SEARCH_ENDPOINT", "https://s10ai003-search.search.windows.net")
search_key = os.getenv("SERACH_AI_KEY")
search_index = os.getenv("SEARCH_INDEX_NAME", "index-10ai003food")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY", "REPLACE_WITH_YOUR_KEY_VALUE_HERE")

# Initialize Azure OpenAI client with key-based authentication
client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=subscription_key,
    api_version="2025-01-01-preview",
)

# IMAGE_PATH = "YOUR_IMAGE_PATH"
# encoded_image = base64.b64encode(open(IMAGE_PATH, 'rb').read()).decode('ascii')

# Prepare the chat prompt
chat_prompt = [
    {
        "role": "system",
        "content": "자취생들을 위한 요리 레시피 및 꿀팁을 알려주는 모델이야. 친절하고 공감되도록 말해줘."
    },
    {
        "role": "user",
        "content": "자취해서 요리하기 힘들더라구! 전자레인지로 할 수 있는 요리 1가지 레시피만 알려줄래?"
    }
]

# Include speech result if speech is enabled
messages = chat_prompt

# Generate the completion
completion = client.chat.completions.create(
    model=deployment,
    messages=messages,
    max_tokens=6553,
    temperature=0.7,
    top_p=0.95,
    frequency_penalty=0,
    presence_penalty=0,
    stop=None,
    stream=False,
    extra_body={
      "data_sources": [{
          "type": "azure_search",
          "parameters": {
            "endpoint": f"{search_endpoint}",
            "index_name": "index-10ai003food",
            "query_type": "simple",
            "fields_mapping": {},
            "in_scope": True,
            "filter": None,
            "strictness": 3,
            "top_n_documents": 5,
            "authentication": {
              "type": "api_key",
              "key": f"{search_key}"
            }
          }
        }]
    }
)

print(completion.choices[0].message.content)
print()

citations = completion.choices[0].message.context.get("citations", [])
filepaths = list({c["filepath"] for c in citations})
print("출처:", filepaths)
    