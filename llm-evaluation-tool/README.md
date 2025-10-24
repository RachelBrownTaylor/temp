# LLM 평가 도구 (LLM Evaluation Tool)

웹 기반 LLM 출력 평가 도구입니다. 모델 응답을 검토하고 별점(1-5점)을 부여할 수 있습니다.

## 주요 기능

- ✅ **사용자 인증**: 평가자/관리자 역할 구분
- ✅ **카테고리별 평가**: 작업 유형별로 예제 분류
- ✅ **멀티턴 대화 지원**: 복잡한 대화 히스토리 표시
- ✅ **별점 평가 시스템**: 1-5점 등급 부여
- ✅ **진행 상황 추적**: 실시간 평가 진행률 확인
- ✅ **관리자 대시보드**: 통계 및 결과 집계
- ✅ **데이터 내보내기**: CSV/JSON 형식 지원
- ✅ **Markdown/LaTeX 렌더링**: 수식 및 코드 블록 표시
- ✅ **Docker 지원**: 컨테이너화된 배포

## 빠른 시작

### Docker 사용 (권장)

1. **이미지 빌드**
```bash
docker build -t llm-eval-tool .
```

2. **컨테이너 실행**
```bash
docker run -d -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/database:/app/database \
  --name llm-eval \
  llm-eval-tool
```

3. **초기 관리자 계정 생성**
```bash
docker exec -it llm-eval python init_admin.py
```

4. **웹 브라우저에서 접속**
```
http://localhost:8080
```

### 로컬 실행

1. **의존성 설치**
```bash
pip install -r requirements.txt
```

2. **초기 사용자 생성**
```bash
python init_admin.py
```

3. **애플리케이션 실행**
```bash
python run.py
```

## 데이터셋 형식

데이터셋은 JSON 파일 형식으로 제공되어야 합니다:

```json
[
  {
    "category": "자연어 번역",
    "history": [
      {"role": "user", "content": "번역해주세요: Hello"}
    ],
    "example_id": 1,
    "responses": [
      {"model": "GPT-5", "output": "안녕하세요"},
      {"model": "Claude", "output": "안녕"}
    ]
  }
]
```

### 필수 필드

- `category` (string): 평가 카테고리
- `history` (array): 대화 히스토리
  - `role` (string): "user" 또는 "assistant"
  - `content` (string): 메시지 내용
- `example_id` (integer): 고유 예제 ID
- `responses` (array): 모델 응답 목록
  - `model` (string): 모델 이름
  - `output` (string): 모델 출력

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `DATABASE_PATH` | SQLite DB 파일 경로 | `/app/database/evaluations.db` |
| `DATASET_PATH` | 평가 데이터셋 JSON 경로 | `/app/data/llm_evaluation.json` |
| `PORT` | 서버 포트 | `8080` |
| `HOST` | 서버 호스트 | `0.0.0.0` |
| `SECRET_KEY` | Flask 세션 비밀키 | `dev-secret-key-change-in-production` |
| `DEBUG` | 디버그 모드 | `False` |

## 사용 방법

### 평가자 워크플로우

1. 로그인
2. 카테고리 선택
3. 대화 히스토리 확인
4. 모델 응답 검토
5. 별점(1-5) 부여 후 저장
6. 다음 예제로 이동

### 관리자 기능

1. **통계 조회**
   - 모델별 평균 점수
   - 카테고리별 평균 점수
   - 교차 분석 (모델 × 카테고리)

2. **데이터 내보내기**
   - CSV 형식: Excel 호환
   - JSON 형식: 프로그래밍 활용

3. **데이터셋 로드**
   - 새 데이터셋 파일 경로 지정
   - 자동 유효성 검사
   - 기존 데이터 교체

## Docker Compose 예제

```yaml
version: '3.8'

services:
  llm-eval:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./database:/app/database
    environment:
      - SECRET_KEY=your-secret-key-here
      - DATABASE_PATH=/app/database/evaluations.db
      - DATASET_PATH=/app/data/llm_evaluation.json
    restart: unless-stopped
```

## 데이터베이스 스키마

### users 테이블
- `id`: 사용자 ID (PK)
- `username`: 사용자명 (UNIQUE)
- `password_hash`: 비밀번호 해시
- `role`: 역할 (evaluator/admin)

### examples 테이블
- `id`: 내부 ID (PK)
- `example_id`: 예제 고유 ID (UNIQUE)
- `category`: 카테고리
- `history`: 대화 히스토리 (JSON)
- `responses`: 모델 응답 목록 (JSON)

### ratings 테이블
- `id`: 평가 ID (PK)
- `user_id`: 평가자 ID (FK)
- `example_id`: 예제 ID (FK)
- `model_name`: 모델 이름
- `rating`: 평점 (1-5)
- `timestamp`: 평가 시간
- UNIQUE(user_id, example_id, model_name)

## 프로덕션 배포 팁

1. **비밀키 변경**
   ```bash
   export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   ```

2. **HTTPS 사용**
   - Nginx 리버스 프록시 설정
   - Let's Encrypt SSL 인증서

3. **데이터 백업**
   ```bash
   # 데이터베이스 백업
   docker exec llm-eval sqlite3 /app/database/evaluations.db .dump > backup.sql
   ```

4. **로그 관리**
   ```bash
   docker logs llm-eval > app.log
   ```

## 트러블슈팅

### 데이터셋이 로드되지 않음
- JSON 형식 검증: https://jsonlint.com/
- 파일 경로 확인: 컨테이너 내부 경로와 볼륨 마운트 확인

### 로그인 실패
- 초기 사용자 생성 확인: `docker exec -it llm-eval python init_admin.py`
- 데이터베이스 권한 확인

### 포트 충돌
```bash
# 다른 포트 사용
docker run -p 9090:8080 ...
```

## 시스템 요구사항

- **Docker**: 20.10 이상
- **Python**: 3.11 이상 (로컬 실행 시)
- **메모리**: 최소 512MB RAM
- **디스크**: 100MB + 데이터셋 크기

## 라이센스

MIT License

## 기여

이슈 및 풀 리퀘스트 환영합니다.

## 지원

문제가 발생하면 GitHub Issues에 등록해주세요.
