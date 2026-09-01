import os
import json
import re
from dotenv import load_dotenv

# 필요한 경우만 사용
# import requests
# from openai import OpenAI

load_dotenv()


def get_user_input():
    """
    사용자 입력을 받고, 중간에 exit 입력 시 None 반환
    """
    companion = input("누구와 가시나요? (혼자/친구/연인/가족, 종료: exit): ").strip()
    if companion.lower() == "exit":
        return None

    budget = input("예산은 얼마인가요? (종료: exit): ").strip()
    if budget.lower() == "exit":
        return None

    days = input("몇 일 여행인가요? (종료: exit): ").strip()
    if days.lower() == "exit":
        return None

    season = input("어느 계절인가요? (종료: exit): ").strip()
    if season.lower() == "exit":
        return None

    style = input("어떤 스타일을 원하나요? (종료: exit): ").strip()
    if style.lower() == "exit":
        return None

    return {
        "companion": companion,
        "budget": budget,
        "days": days,
        "season": season,
        "style": style
    }


def clean_json_text(text):
    """
    모델 응답에서 ```json ... ``` 같은 마크다운 제거
    """
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    return text.strip()


def recommend_travel(user_info):
    """
    여기에 기존 AI 추천 로직을 연결하세요.
    현재는 예시용 구조입니다.

    기존에 이미 OpenAI 호환 API / Codyssey API 연결이 되어 있다면,
    이 함수 안에 그 코드를 넣으면 됩니다.
    """
    # 예시 응답 구조
    return [
        {
            "name": "남이섬",
            "reason": "겨울 감성과 메타세쿼이아길이 인상적이고 가볍게 걷기 좋습니다.",
            "tip": "배편 시간을 미리 확인하면 일정이 더 여유롭습니다.",
            "address": "강원특별자치도 춘천시 남산면 남이섬길 1",
            "url": "http://place.map.kakao.com/11276521"
        },
        {
            "name": "오이도 빨강등대",
            "reason": "바다를 보며 산책하기 좋고, 부담 없는 코스로 즐기기 좋습니다.",
            "tip": "해 질 무렵 방문하면 풍경이 더 좋습니다.",
            "address": "경기 시흥시 오이도로 170",
            "url": "http://place.map.kakao.com/13498966"
        }
    ]


def print_recommendations(recommendations):
    """
    추천 결과를 보기 좋게 출력
    """
    if not recommendations:
        print("추천 결과가 없습니다.")
        return

    print("\n추천 여행지 결과")
    print("-" * 40)

    for idx, place in enumerate(recommendations, start=1):
        print(f"[{idx}] {place.get('name', '이름 없음')}")
        print(f"추천 이유: {place.get('reason', '-')}")
        print(f"여행 팁 : {place.get('tip', '-')}")
        print(f"주소   : {place.get('address', '-')}")
        print(f"지도 링크: {place.get('url', '-')}")
        print("-" * 40)


def main():
    try:
        print("여행지 추천 프로그램입니다.")
        print("중간에 종료하려면 exit를 입력하세요.\n")

        user_info = get_user_input()
        if user_info is None:
            print("프로그램을 종료합니다.")
            return

        print("\n입력 완료!")
        print(user_info)

        recommendations = recommend_travel(user_info)
        print_recommendations(recommendations)

    except KeyboardInterrupt:
        print("\n사용자에 의해 종료되었습니다. 프로그램을 안전하게 닫습니다.")


if __name__ == "__main__":
    main()