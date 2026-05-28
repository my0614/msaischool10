import os
import json
import requests
import time
from openai import AzureOpenAI
from dotenv import load_dotenv
import json

load_dotenv()

client = AzureOpenAI(
  azure_endpoint = os.getenv("ENDPOINT_URL"),
  api_key= os.getenv("ASSISTANT_KEY"),
  api_version="2024-05-01-preview"
)

assistant = client.beta.assistants.create(
  model="gpt-4o-mini-10ai003", # replace with model deployment name.
  instructions="",
  tools=[{"type":"file_search"},{"type":"code_interpreter"}],
  tool_resources={"file_search":{"vector_store_ids":["vs_KLIufR2vUjiOlAFNfhvhqvx5"]},"code_interpreter":{"file_ids":[]}},
  temperature=1,
  top_p=1
)

# Create a thread
thread = client.beta.threads.create()

# Add a user question to the thread
message = client.beta.threads.messages.create(
  thread_id=thread.id,
  role="user",
  content="1부터 100 사이의 소수를 출력해주고, 그래프도 그려줘" # Replace this with your prompt
)

# Run the thread
run = client.beta.threads.runs.create(
  thread_id=thread.id,
  assistant_id=assistant.id
)

# Looping until the run completes or fails
while run.status in ['queued', 'in_progress', 'cancelling']:
  time.sleep(1)
  run = client.beta.threads.runs.retrieve(
    thread_id=thread.id,
    run_id=run.id
  )

if run.status == 'completed':
  messages = client.beta.threads.messages.list(
    thread_id=thread.id
  )
  for content_type in messages.data[0].content:
      if content_type == 'text':
          print("내용",messages.data[0].content[0].text.value)
          print("출처",messages.data[0].content[0].text.value)
      elif content_type == 'image_file':   
        # file_id 추출
        file_id = messages.data[0].content[0].image_file.file_id  # 'assistant-CLc1P5SETN3giZCMcUtGKX'

        # 파일 다운로드
        image_data = client.files.content(file_id)

        # 파일로 저장
        with open("./graph.png", "wb") as f:
            f.write(image_data.content)

        print("graph.png 저장 완료")
  
elif run.status == 'requires_action':
  # the assistant requires calling some functions
  # and submit the tool outputs back to the run
  pass
else:
  print(run.status)
  
# # Create a thread
# thread = client.beta.threads.create()

# # Add a user question to the thread
# message = client.beta.threads.messages.create(
#   thread_id=thread.id,
#   role="user",
#   content="마지 여행사는 어떤 여행지를 서비스해?" # Replace this with your prompt
# )



# # Run the thread
# run = client.beta.threads.runs.create(
#   thread_id=thread.id,
#   assistant_id=assistant.id
# )

# # Looping until the run completes or fails
# while run.status in ['queued', 'in_progress', 'cancelling']:
#   time.sleep(1)
#   run = client.beta.threads.runs.retrieve(
#     thread_id=thread.id,
#     run_id=run.id
#   )

# if run.status == 'completed':
#   messages = client.beta.threads.messages.list(
#     thread_id=thread.id
#   )
#   print("내용",messages.data[0].content[0].text.value)
#   print("출처",messages.data[0].content[0].text.annotations[0].file_citation.file_id)
# elif run.status == 'requires_action':
#   # the assistant requires calling some functions
#   # and submit the tool outputs back to the run
#   pass
# else:
#   print(run.status)