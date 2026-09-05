# 국내 여행지 추천 프로그램

사용자가 입력한 여행 조건을 바탕으로 국내 여행 도시를 추천하고, Kakao Local API로 해당 도시의 맛집을 검색한 뒤 최종 여행 리포트를 생성하는 CLI 기반 Python 프로그램입니다.

## 주요 기능

- CLI 필수 옵션으로 여행 날짜 입력
- 날짜 형식 검증
- 여행 동행, 예산, 기간, 계절, 스타일 입력
- OpenAI API를 이용한 추천 도시 생성
- 추천 도시의 날씨와 행사·축제 후보 생성
- Kakao Local API를 이용한 맛집 5곳 검색
- 오전·점심·오후·저녁 일정이 포함된 최종 리포트 생성
- 실행 결과를 JSON과 Markdown 파일로 저장
- API 및 JSON 파싱 오류 처리

## 사용 기술

- Python 3.10 이상
- OpenAI API
- Kakao Local API
- requests
- python-dotenv
- argparse

## 파일 구성

```text
A2_travel_project/
├─ main.py
├─ README.md
├─ .env
├─ .gitignore
├─ test_kakao.py
├─ test_models.py
└─ results/
```

## 필요한 패키지 설치

터미널에서 다음 명령어를 실행합니다.

```bash
pip install requests python-dotenv openai
```

## API 키 설정

프로젝트 폴더에 `.env` 파일을 만들고 다음과 같이 작성합니다.

```env
OPENAI_API_KEY=본인의_OpenAI_API_키
OPENAI_MODEL=gpt-4o-mini
KAKAO_REST_API_KEY=본인의_Kakao_REST_API_키
```

별도의 OpenAI 호환 API 주소를 사용하는 경우 다음 항목도 추가할 수 있습니다.

```env
OPENAI_BASE_URL=사용할_API_주소
```

API 키는 코드에 직접 입력하지 않고 환경변수로 관리합니다.

## 실행 방법

터미널에서 다음 명령어를 실행합니다.

```bash
python main.py -date 2026-09-10
```

날짜는 반드시 `YYYY-MM-DD` 형식으로 입력해야 합니다.

잘못된 실행 예:

```bash
python main.py -date 2026/09/10
```

날짜 형식이 올바르지 않으면 사용 방법을 안내하고 프로그램을 종료합니다.

## 사용자 입력 항목

프로그램을 실행하면 다음 내용을 차례로 입력합니다.

- 동행
- 예산
- 여행 기간
- 계절
- 여행 스타일

입력 도중 `exit`를 입력하면 프로그램을 종료할 수 있습니다.

## 프로그램 처리 과정

1. CLI에서 여행 날짜를 입력받습니다.
2. 사용자의 여행 조건을 입력받습니다.
3. OpenAI API가 추천 도시, 날씨, 행사, 추천 이유를 JSON으로 생성합니다.
4. JSON 파싱에 실패하면 형식을 강화하여 한 번 재시도합니다.
5. 추천 도시를 기준으로 Kakao Local API에서 맛집을 최대 5곳 검색합니다.
6. 추천 정보와 맛집을 이용하여 최종 여행 리포트를 생성합니다.
7. 결과를 JSON과 Markdown 파일로 저장합니다.

## 결과 파일

실행 결과는 `results` 폴더에 저장됩니다.

```text
results/
├─ travel_data_2026-09-10_실행시간.json
└─ travel_report_2026-09-10_실행시간.md
```

### JSON 파일

다음 내용을 포함합니다.

- 여행 날짜
- 사용자 입력 조건
- 추천 도시·날씨·행사·추천 이유
- 맛집 검색 결과
- 오류 목록
- LLM 원본 응답

### Markdown 파일

다음 내용을 포함합니다.

- 추천 지역과 추천 이유
- 날씨 정보와 준비물
- 행사·축제 후보
- 추천 맛집
- 오전·점심·오후·저녁 일정

## 오류 처리

- OpenAI API 키가 없으면 설정 방법을 안내하고 종료합니다.
- Kakao REST API 키가 없으면 설정 방법을 안내하고 종료합니다.
- LLM의 JSON 파싱에 실패하면 한 번 재시도합니다.
- Kakao API 호출 또는 검색에 실패해도 맛집을 `데이터 없음`으로 처리하고 리포트 생성을 계속합니다.
- 실행 중 수집된 오류는 JSON 파일의 `errors` 배열에 저장됩니다.

## 보안 주의 사항

- API 키를 Python 코드에 직접 작성하지 않습니다.
- `.env` 파일을 GitHub에 업로드하지 않습니다.
- `.gitignore`에 `.env`와 `results/`를 포함합니다.
- README와 실행 화면에도 실제 API 키가 노출되지 않도록 주의합니다.