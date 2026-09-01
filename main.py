import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY", "").strip()
base_url = os.getenv("OPENAI_BASE_URL", "").strip()

print("OPENAI_API_KEY 존재 여부:", bool(api_key))
print("OPENAI_BASE_URL:", base_url)

if not api_key:
    print("OPENAI_API_KEY가 없습니다. .env 파일을 확인하세요.")
    exit()

if not base_url:
    print("OPENAI_BASE_URL이 없습니다. .env 파일을 확인하세요.")
    exit()

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

system_prompt = """
당신은 친절한 국내 여행 추천 도우미입니다.
사용자의 취향, 계절, 동행 인원, 예산을 고려해
한국 여행지 3곳을 추천하세요.

각 여행지마다 아래 내용을 포함하세요:
1. 추천 이유
2. 대표 볼거리
3. 대표 먹거리
4. 간단한 이동 팁

답변은 보기 쉽게 정리하세요.
"""

while True:
    user_input = input("\n어떤 국내 여행지를 추천받고 싶나요? (종료: exit) \n> ").strip()

    if user_input.lower() in ["exit", "quit", "q"]:
        print("프로그램을 종료합니다.")
        break

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )

        answer = response.choices[0].message.content
        print("\n[추천 결과]")
        print(answer)

    except Exception as e:
        print("\nAPI 호출 중 오류가 발생했습니다.")
        print(e)