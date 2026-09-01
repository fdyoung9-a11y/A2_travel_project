# A2_travel_project

Python API를 활용한 국내 여행지 추천 프로그램입니다.

## 프로젝트 소개
이 프로그램은 사용자의 입력을 바탕으로 국내 여행지를 추천하는 것을 목표로 합니다.  
Python과 외부 API를 활용하여 여행지 정보를 가져오고, 추천 결과를 출력합니다.

## 개발 목적
- Python API 활용 연습
- 환경 변수(.env) 관리 방법 학습
- Git과 GitHub 협업 및 버전 관리 연습
- 여행지 추천 프로그램 구현

## 주요 기능
- 사용자 입력 기반 여행 조건 수집
- OpenAI 호환 API로 국내 여행지 추천
- Kakao Local API로 장소 주소 및 지도 링크 출력

## 사용 기술
- Python 3.10+
- requests
- python-dotenv
- openai
- Git / GitHub
- VS Code

## 파일 구성
```bash
A2_travel_project/
├─ main.py
├─ .gitignore
├─ .env   # GitHub에는 업로드되지 않음
└─ README.md