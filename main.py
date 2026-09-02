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
        raise ValueError("날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력하세요.")

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
    모델에게 JSON 형식만 출력하도록 요청하는 프롬프트를 만든다.
    """
    return f"""
너는 한국 국내 여행지 추천 전문가다.

아래 조건에 맞는 여행지를 3곳 추천해라.
반드시 JSON만 출력하고, 설명 문장이나 코드블록(````)은 쓰지 마라.

여행 조건:
- 여행 날짜: {travel_date}
- 동행: {user_input["companion"]}
- 예산: {user_input["budget"]}
- 여행 기간: {user_input["days"]}
- 계절: {user_input["season"]}
- 여행 스타일: {user_input["style"]}

출력 형식:
[
  {{
    "name": "여행지 이름",
    "reason": "추천 이유",
    "tip": "여행 팁",
    "area_hint": "지역 힌트",
    "category": "바다/산/도시/역사/자연/맛집 등"
  }},
  ...
]

주의:
- 반드시 3개 이상 추천
- 한국어로 작성
- JSON 배열만 출력
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


def extract_recommendations_from_text(text):
    """
    LLM 응답 텍스트를 JSON으로 파싱하여 추천 리스트를 반환한다.
    """
    data = extract_json_block(text)

    # {"recommendations": [...]} 또는 {"places": [...]} 형태 허용
    if isinstance(data, dict):
        if "recommendations" in data:
            data = data["recommendations"]
        elif "places" in data:
            data = data["places"]
        else:
            data = [data]

    if not isinstance(data, list):
        raise ValueError("추천 데이터 형식이 올바르지 않습니다. JSON 배열이어야 합니다.")

    normalized = []
    for item in data:
        if not isinstance(item, dict):
            continue

        normalized.append({
            "name": item.get("name") or item.get("title") or "이름 없음",
            "reason": item.get("reason", ""),
            "tip": item.get("tip", ""),
            "area_hint": item.get("area_hint", item.get("area", "")),
            "category": item.get("category", ""),
            "address": item.get("address", ""),
            "url": item.get("url", "")
        })

    if not normalized:
        raise ValueError("추천 결과가 비어 있습니다.")

    return normalized


# --------------------------------------------------
# 5) Kakao Local 검색
# --------------------------------------------------
def search_kakao_place(query):
    """
    Kakao Local API로 장소 검색.
    """
    kakao_key = os.getenv("KAKAO_REST_API_KEY")
    if not kakao_key:
        return None

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {
        "Authorization": f"KakaoAK {kakao_key}"
    }
    params = {
        "query": query,
        "size": 5
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None

    documents = data.get("documents", [])
    if not documents:
        return None

    return documents[0]


def enrich_with_kakao(recommendations):
    """
    추천 장소에 Kakao Local 검색 결과를 덧붙인다.
    """
    enriched = []

    for rec in recommendations:
        query_parts = [rec.get("name", "").strip()]
        area_hint = rec.get("area_hint", "").strip()
        if area_hint:
            query_parts.append(area_hint)

        query = " ".join([part for part in query_parts if part])

        kakao_place = search_kakao_place(query)

        merged = dict(rec)
        if kakao_place:
            merged["kakao_place_name"] = kakao_place.get("place_name", "")
            merged["kakao_address_name"] = kakao_place.get("address_name", "")
            merged["kakao_road_address_name"] = kakao_place.get("road_address_name", "")
            merged["kakao_phone"] = kakao_place.get("phone", "")
            merged["kakao_place_url"] = kakao_place.get("place_url", "")
            merged["x"] = kakao_place.get("x", "")
            merged["y"] = kakao_place.get("y", "")
        else:
            merged["kakao_place_name"] = ""
            merged["kakao_address_name"] = ""
            merged["kakao_road_address_name"] = ""
            merged["kakao_phone"] = ""
            merged["kakao_place_url"] = ""

        enriched.append(merged)

    return enriched


# --------------------------------------------------
# 6) 출력 및 저장
# --------------------------------------------------
def print_recommendations(travel_date, user_input, recommendations):
    """
    콘솔에 보기 좋게 출력한다.
    """
    print("\n" + "=" * 60)
    print(f"여행 날짜: {travel_date}")
    print(f"동행: {user_input['companion']}")
    print(f"예산: {user_input['budget']}")
    print(f"기간: {user_input['days']}일")
    print(f"계절: {user_input['season']}")
    print(f"스타일: {user_input['style']}")
    print("=" * 60)

    for idx, rec in enumerate(recommendations, start=1):
        print(f"\n[{idx}] {rec.get('name', '이름 없음')}")
        if rec.get("category"):
            print(f" - 분류: {rec['category']}")
        if rec.get("area_hint"):
            print(f" - 지역 힌트: {rec['area_hint']}")
        if rec.get("reason"):
            print(f" - 추천 이유: {rec['reason']}")
        if rec.get("tip"):
            print(f" - 여행 팁: {rec['tip']}")
        if rec.get("kakao_place_name"):

                       print(f" - 카카오 장소명: {rec['kakao_place_name']}")
        if rec.get("kakao_address_name"):
            print(f" - 주소: {rec['kakao_address_name']}")
        if rec.get("kakao_road_address_name"):
            print(f" - 도로명 주소: {rec['kakao_road_address_name']}")
        if rec.get("kakao_phone"):
            print(f" - 전화번호: {rec['kakao_phone']}")
        if rec.get("kakao_place_url"):
            print(f" - 장소 URL: {rec['kakao_place_url']}")


def build_markdown_report(travel_date, user_input, recommendations):
    """
    Markdown 리포트 문자열 생성
    """
    lines = []
    lines.append(f"# 여행지 추천 리포트")
    lines.append("")
    lines.append(f"- 여행 날짜: {travel_date}")
    lines.append(f"- 동행: {user_input['companion']}")
    lines.append(f"- 예산: {user_input['budget']}")
    lines.append(f"- 기간: {user_input['days']}일")
    lines.append(f"- 계절: {user_input['season']}")
    lines.append(f"- 스타일: {user_input['style']}")
    lines.append("")
    lines.append("## 추천 결과")
    lines.append("")

    for idx, rec in enumerate(recommendations, start=1):
        lines.append(f"### {idx}. {rec.get('name', '이름 없음')}")
        if rec.get("category"):
            lines.append(f"- 분류: {rec['category']}")
        if rec.get("area_hint"):
            lines.append(f"- 지역 힌트: {rec['area_hint']}")
        if rec.get("reason"):
            lines.append(f"- 추천 이유: {rec['reason']}")
        if rec.get("tip"):
            lines.append(f"- 여행 팁: {rec['tip']}")
        if rec.get("kakao_place_name"):
            lines.append(f"- 카카오 장소명: {rec['kakao_place_name']}")
        if rec.get("kakao_address_name"):
            lines.append(f"- 주소: {rec['kakao_address_name']}")
        if rec.get("kakao_road_address_name"):
            lines.append(f"- 도로명 주소: {rec['kakao_road_address_name']}")
        if rec.get("kakao_phone"):
            lines.append(f"- 전화번호: {rec['kakao_phone']}")
        if rec.get("kakao_place_url"):
            lines.append(f"- 장소 URL: {rec['kakao_place_url']}")
        lines.append("")

    return "\n".join(lines)


def save_results(travel_date, user_input, recommendations, raw_text):
    """
    결과를 results 폴더에 JSON / Markdown으로 저장
    """
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = str(travel_date)

    json_path = results_dir / f"travel_recommendation_{date_str}_{timestamp}.json"
    md_path = results_dir / f"travel_recommendation_{date_str}_{timestamp}.md"

    payload = {
        "travel_date": date_str,
        "user_input": user_input,
        "recommendations": recommendations,
        "raw_text": raw_text
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    markdown_text = build_markdown_report(travel_date, user_input, recommendations)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)

    return json_path, md_path


# --------------------------------------------------
# 7) 메인 실행
# --------------------------------------------------
def main():
    try:
        travel_date = parse_args()
        user_input = get_user_input()

        if user_input is None:
            print("프로그램을 종료합니다.")
            return

        print("\n추천 중입니다. 잠시만 기다려 주세요...")

        raw_text = call_openai_recommendation(travel_date, user_input)
        recommendations = extract_recommendations_from_text(raw_text)
        recommendations = enrich_with_kakao(recommendations)

        print_recommendations(travel_date, user_input, recommendations)

        json_path, md_path = save_results(travel_date, user_input, recommendations, raw_text)

        print("\n결과 저장 완료!")
        print(f"- JSON: {json_path}")
        print(f"- Markdown: {md_path}")

    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main()