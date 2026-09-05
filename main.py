import os
import re
import json
import argparse
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일 불러오기
load_dotenv()


# --------------------------------------------------
# 1) CLI 인자 처리
# --------------------------------------------------
def parse_args():
    """
    여행 날짜를 -date / --date 형태로 입력받는다.
    예: python main.py -date 2026-09-02
    """
    parser = argparse.ArgumentParser(description="국내 여행지 추천 CLI 프로그램")
    parser.add_argument(
        "-date", "--date",
        dest="travel_date",
        required=True,
        help="여행 날짜를 입력하세요. 형식: YYYY-MM-DD"
    )

    args = parser.parse_args()

    try:
        travel_date = datetime.strptime(args.travel_date, "%Y-%m-%d").date()
    except ValueError:
        parser.error(
            "날짜 형식이 올바르지 않습니다. "
            "YYYY-MM-DD 형식으로 입력하세요."
    )

    return travel_date


# --------------------------------------------------
# 2) 사용자 입력
# --------------------------------------------------
def get_user_input():
    """
    사용자에게 여행 조건을 묻고 입력값을 받는다.
    중간에 exit 입력 시 종료한다.
    """
    print("\n여행지 추천 프로그램입니다.")
    print("중간에 종료하려면 exit를 입력하세요.\n")

    def ask(prompt):
        while True:
            value = input(prompt).strip()
            if value.lower() == "exit":
                return None
            if value:
                return value
            print("값을 비워둘 수 없습니다.")

    companion = ask("누구와 가시나요? (혼자/친구/연인/가족, 종료: exit): ")
    if companion is None:
        return None

    budget = ask("예산은 얼마인가요? (종료: exit): ")
    if budget is None:
        return None

    days = ask("몇 일 여행인가요? (종료: exit): ")
    if days is None:
        return None

    season = ask("어느 계절인가요? (종료: exit): ")
    if season is None:
        return None

    style = ask("어떤 스타일을 원하나요? (종료: exit): ")
    if style is None:
        return None

    return {
        "companion": companion,
        "budget": budget,
        "days": days,
        "season": season,
        "style": style
    }


# --------------------------------------------------
# 3) OpenAI 설정 및 호출
# --------------------------------------------------
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY가 설정되어 있지 않습니다.")

    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)

    return OpenAI(api_key=api_key)


def build_prompt(travel_date, user_input):
    """
    모델에게 추천 도시, 날씨, 행사 정보를
    JSON 형식으로 요청하는 프롬프트를 만든다.
    """
    return f"""
너는 한국 국내 여행 전문가다.

아래 여행 조건을 분석하여 가장 적합한 국내 여행 도시 1곳을 추천해라.
반드시 JSON 객체만 출력하고 설명 문장이나 코드블록은 작성하지 마라.

여행 조건:
- 여행 날짜: {travel_date}
- 동행: {user_input["companion"]}
- 예산: {user_input["budget"]}
- 여행 기간: {user_input["days"]}
- 계절: {user_input["season"]}
- 여행 스타일: {user_input["style"]}

반드시 다음 JSON 형식으로 출력해라.

{{
  "recommended_city": "추천 도시 이름",
  "weather": "해당 시기의 일반적인 날씨 요약",
  "events": [
    "행사 또는 축제 후보 1",
    "행사 또는 축제 후보 2"
  ],
  "reason": "이 도시를 추천하는 이유를 2~4문장으로 작성"
}}

필수 규칙:
- recommended_city는 국내 도시 1곳만 작성
- weather는 문자열로 작성
- events는 1~3개의 문자열이 담긴 배열로 작성
- reason은 2~4문장으로 작성
- 확인되지 않은 행사는 후보 또는 예상 정보라고 표시
- 반드시 한국어로 작성
- JSON 이외의 내용은 출력하지 말 것
""".strip()


def call_openai_recommendation(travel_date, user_input):
    """
    OpenAI API를 호출해 여행지 추천 JSON을 받는다.
    """
    client = get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    prompt = build_prompt(travel_date, user_input)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "너는 여행지 추천을 잘하는 한국어 비서다. 반드시 JSON만 출력한다."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI 응답이 비어 있습니다.")

    return content


# --------------------------------------------------
# 4) JSON 정리 및 파싱
# --------------------------------------------------
def clean_json_text(text):
    """
    ```json ... ``` 형태나 앞뒤 불필요한 문장을 정리한다.
    """
    text = text.strip()

    # 코드블록 제거
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    return text.strip()


def extract_json_block(text):
    """
    응답 텍스트에서 JSON 덩어리를 최대한 찾아낸다.
    """
    cleaned = clean_json_text(text)

    # 먼저 그대로 파싱 시도
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # JSON 배열 또는 객체를 찾아서 다시 시도
    array_match = re.search(r"\[[\s\S]*\]", cleaned)
    if array_match:
        candidate = array_match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    object_match = re.search(r"\{[\s\S]*\}", cleaned)
    if object_match:
        candidate = object_match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError("LLM 응답에서 유효한 JSON을 추출할 수 없습니다.")


def extract_recommendation_from_text(text):
    """
    LLM 응답을 JSON으로 파싱하고 필수 항목을 확인한다.
    """
    data = extract_json_block(text)

    if not isinstance(data, dict):
        raise ValueError("추천 결과는 JSON 객체 형식이어야 합니다.")

    required_keys = [
        "recommended_city",
        "weather",
        "events",
        "reason"
    ]

    missing_keys = [
        key for key in required_keys
        if key not in data
    ]

    if missing_keys:
        raise ValueError(
            "필수 항목이 없습니다: " + ", ".join(missing_keys)
        )

    if not isinstance(data["events"], list):
        raise ValueError("events 항목은 배열 형식이어야 합니다.")

    recommendation = {
        "recommended_city": str(data["recommended_city"]).strip(),
        "weather": str(data["weather"]).strip(),
        "events": [
            str(event).strip()
            for event in data["events"]
            if str(event).strip()
        ],
        "reason": str(data["reason"]).strip()
    }

    if not recommendation["recommended_city"]:
        raise ValueError("추천 도시가 비어 있습니다.")

    return recommendation

def retry_openai_recommendation(travel_date, user_input):
    """
    JSON 파싱 실패 시 형식을 더 강하게 지정하여
    OpenAI API를 한 번 더 호출한다.
    """
    client = get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    prompt = build_prompt(travel_date, user_input)

    retry_prompt = f"""
{prompt}

이전 응답은 JSON 형식 오류로 파싱하지 못했다.
이번에는 다음 규칙을 반드시 지켜라.

- JSON 객체 하나만 출력할 것
- 코드블록을 사용하지 말 것
- JSON 앞뒤에 설명을 쓰지 말 것
- recommended_city, weather, events, reason을 모두 포함할 것
- events는 반드시 문자열 배열로 작성할 것
""".strip()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "반드시 파싱 가능한 올바른 JSON 객체만 "
                    "출력하는 한국어 여행 추천 비서다."
                )
            },
            {
                "role": "user",
                "content": retry_prompt
            }
        ],
        temperature=0.2
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("재시도한 OpenAI 응답이 비어 있습니다.")

    return content


def get_recommendation_with_retry(
    travel_date,
    user_input,
    errors
):
    """
    여행 추천을 요청하고 JSON 파싱에 실패하면
    프롬프트를 강화하여 한 번 재시도한다.
    """
    raw_text = call_openai_recommendation(
        travel_date,
        user_input
    )

    try:
        recommendation = extract_recommendation_from_text(
            raw_text
        )
        return raw_text, recommendation

    except ValueError as first_error:
        error_message = (
            f"첫 번째 LLM JSON 파싱 실패: {first_error}"
        )
        print(error_message)
        errors.append(error_message)

    retry_text = retry_openai_recommendation(
        travel_date,
        user_input
    )

    try:
        recommendation = extract_recommendation_from_text(
            retry_text
        )
        return retry_text, recommendation

    except ValueError as second_error:
        error_message = (
            f"두 번째 LLM JSON 파싱 실패: {second_error}"
        )
        errors.append(error_message)
        raise ValueError(error_message)
# --------------------------------------------------
# 5) Kakao Local 검색
# --------------------------------------------------
def search_kakao_restaurants(city, errors):
    """
    추천 도시를 기준으로 Kakao Local API에서
    맛집을 최대 5곳까지 검색한다.
    """
    kakao_key = os.getenv("KAKAO_REST_API_KEY")

    if not kakao_key:
        raise EnvironmentError(
            "KAKAO_REST_API_KEY가 설정되어 있지 않습니다. "
            ".env 파일을 확인하세요."
        )

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"

    headers = {
        "Authorization": f"KakaoAK {kakao_key}"
    }

    params = {
        "query": f"{city} 맛집",
        "size": 5
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

    except requests.RequestException as e:
        error_message = f"Kakao Local API 호출 실패: {e}"
        print(error_message)
        errors.append(error_message)
        return []

    documents = data.get("documents", [])

    if not documents:
        print(f"{city}의 맛집 검색 결과가 없습니다.")
        return []

    restaurants = []

    for place in documents[:5]:
        restaurants.append({
            "name": place.get("place_name", ""),
            "address": (
                place.get("road_address_name")
                or place.get("address_name", "")
            ),
            "category": place.get("category_name", ""),
            "url": place.get("place_url", ""),
            "x": place.get("x", ""),
            "y": place.get("y", "")
        })

    return restaurants

def generate_final_report(
    travel_date,
    user_input,
    recommendation,
    restaurants
):
    """
    추천 정보와 맛집 검색 결과를 이용하여
    최종 여행 리포트를 Markdown 형식으로 생성한다.
    """
    client = get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    recommendation_json = json.dumps(
        recommendation,
        ensure_ascii=False,
        indent=2
    )

    restaurants_json = json.dumps(
        restaurants,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
너는 한국 국내 여행 일정 설계 전문가다.

아래 정보를 이용하여 최종 여행 리포트를
Markdown 형식으로 작성해라.

여행 날짜:
{travel_date}

여행 조건:
- 동행: {user_input["companion"]}
- 예산: {user_input["budget"]}
- 여행 기간: {user_input["days"]}
- 계절: {user_input["season"]}
- 여행 스타일: {user_input["style"]}

1차 여행 추천 JSON:
{recommendation_json}

맛집 검색 결과:
{restaurants_json}

리포트에는 다음 항목을 반드시 포함해라.

# 국내 여행 추천 리포트

## 1. 추천 지역
- 추천 도시
- 추천 이유

## 2. 날씨 정보
- 해당 시기의 일반적인 날씨
- 준비하면 좋은 물품

## 3. 행사 및 축제
- 행사 또는 축제 후보
- 실제 개최 여부는 방문 전 확인이 필요하다고 안내

## 4. 추천 맛집
- 맛집 이름
- 주소
- 음식 분류
- 장소 URL
- 맛집 결과가 빈 배열이면 "데이터 없음"으로 표시

## 5. 1일 추천 일정
- 오전 일정
- 점심 일정
- 오후 일정
- 저녁 일정

주의:
- 제공된 정보에 없는 맛집 이름과 주소를 임의로 만들지 말 것
- 확인되지 않은 행사 일정을 확정적으로 표현하지 말 것
- 읽기 쉬운 한국어 Markdown 형식으로 작성할 것
""".strip()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "너는 제공된 데이터를 근거로 "
                    "국내 여행 리포트를 작성하는 한국어 비서다."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.5
    )

    report = response.choices[0].message.content

    if not report:
        raise ValueError("최종 여행 리포트가 비어 있습니다.")

    return report.strip()
# --------------------------------------------------
# 6) 출력 및 저장
# --------------------------------------------------
def print_results(
    travel_date,
    user_input,
    recommendation,
    restaurants
):
    """
    추천 결과와 맛집 목록을 콘솔에 출력한다.
    """
    print("\n" + "=" * 60)
    print("국내 여행 추천 결과")
    print("=" * 60)

    print(f"여행 날짜: {travel_date}")
    print(f"동행: {user_input['companion']}")
    print(f"예산: {user_input['budget']}")
    print(f"기간: {user_input['days']}")
    print(f"계절: {user_input['season']}")
    print(f"스타일: {user_input['style']}")

    print("\n[추천 지역]")
    print(recommendation["recommended_city"])

    print("\n[추천 이유]")
    print(recommendation["reason"])

    print("\n[날씨 요약]")
    print(recommendation["weather"])

    print("\n[행사 및 축제]")
    events = recommendation.get("events", [])

    if events:
        for event in events:
            print(f"- {event}")
    else:
        print("- 데이터 없음")

    print("\n[추천 맛집]")

    if restaurants:
        for index, restaurant in enumerate(restaurants, start=1):
            print(f"\n{index}. {restaurant['name']}")
            print(f"   주소: {restaurant['address']}")
            print(f"   분류: {restaurant['category']}")
            print(f"   URL: {restaurant['url']}")
    else:
        print("- 데이터 없음")


def save_results(
    travel_date,
    user_input,
    recommendation,
    restaurants,
    raw_text,
    final_report,
    errors=None
):
    """
    원본 데이터를 JSON으로 저장하고
    최종 여행 리포트를 Markdown 파일로 저장한다.
    """
    if errors is None:
        errors = []

    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = str(travel_date)

    json_path = (
        results_dir
        / f"travel_data_{date_str}_{timestamp}.json"
    )

    md_path = (
        results_dir
        / f"travel_report_{date_str}_{timestamp}.md"
    )

    payload = {
        "travel_date": date_str,
        "user_input": user_input,
        "recommendation": recommendation,
        "restaurants": restaurants,
        "errors": errors,
        "raw_llm_response": raw_text
    }

    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(
            payload,
            json_file,
            ensure_ascii=False,
            indent=2
        )

    with open(md_path, "w", encoding="utf-8") as md_file:
        md_file.write(final_report)

    return json_path, md_path


# --------------------------------------------------
# 7) 메인 실행
# --------------------------------------------------
def main():
    try:
        errors = []

        travel_date = parse_args()
        user_input = get_user_input()

        if user_input is None:
            print("프로그램을 종료합니다.")
            return

        print("\n추천 중입니다. 잠시만 기다려 주세요...")

        raw_text, recommendation = get_recommendation_with_retry(
            travel_date,
            user_input,
            errors
)

        city = recommendation["recommended_city"]
        restaurants = search_kakao_restaurants(city, errors)

        final_report = generate_final_report(
            travel_date,
            user_input,
            recommendation,
            restaurants
)
        print_results(
            travel_date,
            user_input,
            recommendation,
            restaurants
        )

        json_path, md_path = save_results(
            travel_date,
            user_input,
            recommendation,
            restaurants,
            raw_text,
            final_report,
            errors
        )
      

        print("\n결과 저장 완료!")
        print(f"- JSON: {json_path}")
        print(f"- Markdown: {md_path}")

    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main()