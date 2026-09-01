# A2_travel_project

Python API를 활용한 국내 여행지 추천 프로그램입니다.

## 프로젝트 소개
이 프로그램은 사용자의 입력을 바탕으로 국내 여행지를 추천하고,  
OpenAI 호환 API를 통해 추천 이유와 여행 팁을 생성합니다.  
또한 Kakao Local API를 활용해 장소의 주소와 지도 링크를 출력합니다.

## 개발 목적
- Python API 활용 연습
- 환경 변수(.env) 관리 방법 학습
- Git/GitHub 협업 및 버전 관리 연습
- 여행지 추천 프로그램 구현

## 주요 기능
- 사용자 입력 기반 여행 조건 수집
- OpenAI 호환 API로 국내 여행지 추천
- Kakao Local API로 장소 주소 및 지도 링크 출력
- 추천 이유와 여행 팁 제공

## 사용 기술
- Python 3.10+
- requests
- python-dotenv
- openai
- Git / GitHub
- VS Code

## 환경 변수
다음 값이 `.env` 파일에 설정되어 있어야 합니다.

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `KAKAO_REST_API_KEY`

A2_travel_project/
 ├─ main.py
 ├─ README.md
 ├─ .env
 ├─ .gitignore
 ├─ test_kakao.py
 └─ test_models.py

## 실행 방법
1. 필요한 패키지를 설치합니다.
   ```bash
   pip install requests python-dotenv openai