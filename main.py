import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY", "").strip()
base_url = os.getenv("OPENAI_BASE_URL", "").strip()

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
당신은 친절한 국내 여행 추천 전문가입니다.
사용자의 여행 조건을 바탕으로 한국 여행지 3곳을 추천하세요.

반드시 아래 형식으로 답변하세요.

[여행지 이름]
- 추천 이유:
- 대표 볼거리:
- 대표 먹거리:
- 예상 분위기:
- 이동 팁:
- 추천 여행 기간:

마지막에는
[한 줄 요약]
도 추가하세요.

답변은 이해하기 쉽게 한국어로 작성하세요.
"""

def ask_input(message):
    value = input(message).strip()
    if value.lower() in ["exit", "quit", "q"]:
        print("프로그램을 종료합니다.")
        exit()
    return value

while True:
    print("\n=== 국내 여행 추천 프로그램 ===")
    print("언제든 종료하려면 exit 를 입력하세요.\n")

    companion = ask_input("누구와 가나요? (혼자/친구/가족/연인): ")
    budget = ask_input("예산은 어느 정도인가요? (저예산/중간/여유): ")
    days = ask_input("여행 기간은 얼마나 되나요? (당일치기/1박2일/2박3일): ")
    season = ask_input("어느 계절에 가나요? (봄/여름/가을/겨울): ")
    style = ask_input("원하는 여행 스타일은 무엇인가요? (바다/산/도시/힐링/먹방/역사): ")

    user_prompt = f"""
    여행 조건:
    - 동행: {companion}
    - 예산: {budget}
    - 기간: {days}
    - 계절: {season}
    - 스타일: {style}

    위 조건에 맞는 국내 여행지 3곳을 추천해주세요.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        answer = response.choices[0].message.content

        print("\n[추천 결과]")
        print(answer)

    except Exception as e:
        print("\nAPI 호출 중 오류가 발생했습니다.")
        print(e)

    again = input("\n다시 추천받을까요? (y/n): ").strip().lower()
    if again != "y":
        print("프로그램을 종료합니다.")
        break