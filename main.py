import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# 환경변수 불러오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "").strip()
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "").strip()

# OpenAI 호환 클라이언트 생성
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)


def get_user_input():
    """사용자 여행 조건 입력 받기"""
    print("국내 여행지 추천 프로그램")
    print("-" * 30)

    companion = input("누구와 가시나요? (혼자/친구/연인/가족): ").strip()
    budget = input("예산은 어느 정도인가요? (예: 10만원, 30만원): ").strip()
    duration = input("여행 기간은 얼마나 되나요? (예: 당일치기, 1박2일): ").strip()
    season = input("어느 계절에 가시나요? (봄/여름/가을/겨울): ").strip()
    style = input("어떤 여행 스타일을 원하시나요? (예: 힐링, 맛집, 자연, 역사, 액티비티): ").strip()

    return {
        "companion": companion,
        "budget": budget,
        "duration": duration,
        "season": season,
        "style": style
    }


def clean_json_text(text):
    """모델 응답에서 ```json ... ``` 같은 마크다운 제거"""
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]

        text = "\n".join(lines).strip()

        if text.startswith("json"):
            text = text[4:].strip()

    return text


def get_ai_recommendations(user_info):
    """AI에게 여행지 3곳 추천받기"""
    prompt = f"""
당신은 국내 여행 전문 큐레이터입니다.
사용자 조건에 맞는 대한민국 여행지 3곳을 추천하세요.

사용자 조건:
- 동행: {user_info['companion']}
- 예산: {user_info['budget']}
- 기간: {user_info['duration']}
- 계절: {user_info['season']}
- 스타일: {user_info['style']}

중요 규칙:
1. 반드시 한국의 실제 여행지/관광지명으로 추천하세요.
2. 카카오 로컬 API에서 검색 가능한 구체적인 장소명으로 작성하세요.
3. 반드시 JSON만 출력하세요.
4. 설명은 짧고 명확하게 작성하세요.

출력 형식:
{{
  "recommendations": [
    {{
      "name": "장소명",
      "reason": "추천 이유",
      "tip": "한 줄 팁"
    }},
    {{
      "name": "장소명",
      "reason": "추천 이유",
      "tip": "한 줄 팁"
    }},
    {{
      "name": "장소명",
      "reason": "추천 이유",
      "tip": "한 줄 팁"
    }}
  ]
}}
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "당신은 국내 여행 추천 도우미입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    content = response.choices[0].message.content
    cleaned = clean_json_text(content)

    data = json.loads(cleaned)
    return data["recommendations"]


def search_kakao_place(query):
    """카카오 Local API로 장소 검색"""
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {
        "Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"
    }
    params = {
        "query": query,
        "size": 1
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    documents = data.get("documents", [])

    if not documents:
        return None

    place = documents[0]
    return {
        "place_name": place.get("place_name"),
        "address_name": place.get("address_name"),
        "road_address_name": place.get("road_address_name"),
        "place_url": place.get("place_url")
    }


def print_results(recommendations):
    """추천 결과 + 카카오 검색 결과 출력"""
    print("\n추천 여행지 결과")
    print("=" * 40)

    for i, rec in enumerate(recommendations, start=1):
        print(f"\n[{i}] {rec['name']}")
        print(f"추천 이유: {rec['reason']}")
        print(f"여행 팁 : {rec['tip']}")

        try:
            place_info = search_kakao_place(rec["name"])

            if place_info:
                address = place_info["road_address_name"] or place_info["address_name"]
                print(f"주소     : {address}")
                print(f"지도 링크: {place_info['place_url']}")
            else:
                print("주소     : 카카오 검색 결과 없음")
        except Exception as e:
            print("카카오 장소 검색 실패:", e)

def search_kakao_place(query):
    if not KAKAO_REST_API_KEY:
        return None

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {
        "Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"
    }
    params = {
        "query": query,
        "size": 1
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    documents = data.get("documents", [])

    if not documents:
        return None

    place = documents[0]
    return {
        "place_name": place.get("place_name"),
        "address_name": place.get("address_name"),
        "road_address_name": place.get("road_address_name"),
        "place_url": place.get("place_url")
    }        


def main():
    # 필수 값 체크
    if not OPENAI_API_KEY:
        print("OPENAI_API_KEY가 없습니다. .env 파일을 확인하세요.")
        return
    if not OPENAI_BASE_URL:
        print("OPENAI_BASE_URL이 없습니다. .env 파일을 확인하세요.")
        return
    if not OPENAI_MODEL:
        print("OPENAI_MODEL이 없습니다. .env 파일을 확인하세요.")
        return
    if not KAKAO_REST_API_KEY:
        print("KAKAO_REST_API_KEY가 없습니다. .env 파일을 확인하세요.")
        return

    try:
        user_info = get_user_input()
        recommendations = get_ai_recommendations(user_info)
        print_results(recommendations)

    except json.JSONDecodeError:
        print("AI 응답을 JSON으로 해석하지 못했습니다. 프롬프트를 다시 조정해보세요.")
    except Exception as e:
        print("프로그램 실행 중 오류가 발생했습니다.")
        print(e)



if __name__ == "__main__":
    main()
