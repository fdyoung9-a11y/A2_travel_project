import requests
from dotenv import load_dotenv
import os

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
kakao_key = os.getenv("KAKAO_REST_API_KEY")

print("라이브러리 import 성공")
print("OpenAI 키 존재 여부:", bool(openai_key))
print("Kakao 키 존재 여부:", bool(kakao_key))