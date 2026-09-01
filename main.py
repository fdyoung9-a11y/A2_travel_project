import os
from dotenv import load_dotenv
from openai import OpenAI


def get_user_input():
    print("=== 국내 여행지 추천 프로그램 ===")
    region = input("가고 싶은 지역을 입력하세요 (예: 강원도, 부산, 제주): ")
    theme = input("원하는 여행 스타일을 입력하세요 (예: 자연, 맛집, 힐링, 액티비티): ")
    days = input("여행 기간을 입력하세요 (예: 1박 2일, 2박 3일): ")

    return region, theme, days


def create_prompt(region, theme, days):
    prompt = f"""
사용자에게 국내 여행지를 추천해주세요.

조건:
- 지역: {region}
- 여행 스타일: {theme}
- 여행 기간: {days}

다음 형식으로 답해주세요:
1. 여행지 이름
2. 추천 이유
3. 주요 볼거리
4. 추천 활동

3곳 추천해주세요.
답변은 한국어로 해주세요.
"""
    return prompt


def get_travel_recommendation(prompt):
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    print("키 앞부분:", api_key[:10] if api_key else "없음")
    print("키 길이:", len(api_key))

    if not api_key:
        print("오류: OPENAI_API_KEY를 찾을 수 없습니다.")
        print(".env 파일을 확인해주세요.")
        return None

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "너는 친절한 국내 여행 추천 도우미야."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7
        )

        result = response.choices[0].message.content
        return result

    except Exception as e:
        print("API 호출 중 오류가 발생했습니다.")
        print("오류 내용:", e)
        return None


def main():
    region, theme, days = get_user_input()
    prompt = create_prompt(region, theme, days)

    print("\n여행지를 추천하는 중입니다...\n")

    result = get_travel_recommendation(prompt)

    if result:
        print("=== 추천 결과 ===")
        print(result)
    else:
        print("추천 결과를 가져오지 못했습니다.")


if __name__ == "__main__":
    main()