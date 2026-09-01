import os
import requests
from dotenv import load_dotenv

load_dotenv()

kakao_api_key = os.getenv("KAKAO_REST_API_KEY", "").strip()

if not kakao_api_key:
    print("KAKAO_REST_API_KEY가 없습니다. .env 파일을 확인하세요.")
    exit()

url = "https://dapi.kakao.com/v2/local/search/keyword.json"
headers = {
    "Authorization": f"KakaoAK {kakao_api_key}"
}
params = {
    "query": "경복궁"
}

try:
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    documents = data.get("documents", [])

    if not documents:
        print("검색 결과가 없습니다.")
    else:
        print("카카오 API 연결 성공!")
        for place in documents[:3]:
            print("- 장소명:", place.get("place_name"))
            print("  주소:", place.get("address_name"))
            print("  URL :", place.get("place_url"))
            print()

except Exception as e:
    print("카카오 API 호출 실패")
    print(e)