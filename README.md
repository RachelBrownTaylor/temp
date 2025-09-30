# MCQ 웹 도구

이 애플리케이션은 다중 선택형 문항(MCQ)을 순차적으로 풀고, 진행 상황을 확인하며, 관리자 기능을 통해 응답을 관리할 수 있는 간단한 웹 서비스입니다.

## 주요 기능

- SQLite 기반 사용자/문항/응답 저장
- 사용자/관리자 역할별 로그인
- 문항별 응답 저장 및 진행 현황 표시
- 관리자용 성적표, 문항 통계, CSV/JSON 내보내기
- 관리자용 JSON 문항 데이터 로드

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=adminpass
export DEFAULT_USER_USERNAME=testuser
export DEFAULT_USER_PASSWORD=testpass
export DATASET_PATH=/path/to/questions.json  # 선택 사항
python app.py
```

기본 포트는 `8080`이며 `PORT` 환경 변수를 통해 변경할 수 있습니다.

## Docker 실행

```bash
docker build -t mcq-app .

docker run -d -p 8080:8080 \
  -v /path/to/data:/app/data \
  -e DB_PATH=/app/data/app.db \
  -e DATASET_PATH=/app/data/questions.json \
  -e ADMIN_USERNAME=admin \
  -e ADMIN_PASSWORD=adminpass \
  -e DEFAULT_USER_USERNAME=testuser \
  -e DEFAULT_USER_PASSWORD=testpass \
  mcq-app
```

- `DB_PATH`는 SQLite 데이터베이스 파일 경로를 지정합니다.
- `DATASET_PATH`가 지정되면 초기 실행 시 문항이 자동으로 로드됩니다.
- `ADMIN_USERNAME`, `ADMIN_PASSWORD`는 최초 관리자 계정을 만듭니다.

## 문항 JSON 형식

```json
[
  {
    "numbering_temp": 1,
    "id": 1225,
    "topic": "MONSTER",
    "question": "개선 방안에 대한 설명으로 옳은 것은? (가) 중심 영역 (나) 가장자리 (다) 두 영역 공통",
    "choices": [
      "가, 나 만 옳음",
      "가, 다 만 옳음",
      "나, 다 만 옳음",
      "가, 나, 다 모두 옳음",
      "가, 나, 다 모두 옳지 않음"
    ],
    "answer": 3
  }
]
```

## 관리자 전용 기능

- `/admin` 페이지에서 응답 결과와 문항 통계를 확인할 수 있습니다.
- `/admin/load` 페이지에서 서버에 존재하는 JSON 파일 경로를 입력하면 문항을 교체할 수 있습니다. 이때 기존 응답은 삭제됩니다.
- `/admin/export?format=csv` 또는 `format=json`으로 결과를 다운로드할 수 있습니다.

## 비고

- UI 텍스트는 모두 한국어로 제공됩니다.
- 세션은 쿠키 기반 Flask 세션을 사용합니다.
