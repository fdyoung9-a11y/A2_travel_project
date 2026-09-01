import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

try:
    models = client.models.list()
    print("모델 조회 성공!")
    for model in models.data:
        print(model.id)
except Exception as e:
    print("모델 조회 실패")
    print(e)