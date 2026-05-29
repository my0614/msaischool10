
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("ENDPOINT_URL")
deployment = os.getenv("DEPLOYMENT_NAME")
search_endpoint = os.getenv("SEARCH_ENDPOINT", "https://10ai003-search.search.windows.net")
search_key = os.getenv("SERACH_AI_KEY")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=subscription_key,
    api_version="2025-01-01-preview",
)

chat_prompt = [
    {
        "role": "system",
        "content": "너는 영화 관련 도우미야."
    },
    {
        "role": "user",
        "content": "영화 추천해줘"
    },
    {
        "role": "assistant",
        "content": "기생충, 인셉션, 인터스텔라 등을 추천해요! 어떤 장르를 좋아하세요?"
    },
    {
        "role": "user",
        "content": "액션 영화로 추천해줘"
    }
]

completion = client.chat.completions.create(
    model=deployment,
    messages=chat_prompt,
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
                "endpoint": search_endpoint,
                "index_name": "rag-1780035521025",
                "semantic_configuration": "rag-1780035521025-semantic-configuration",
                "query_type": "semantic",
                "fields_mapping": {},
                "in_scope": True,
                "filter": None,
                "strictness": 3,
                "top_n_documents": 5,
                "authentication": {
                    "type": "api_key",
                    "key": search_key
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
