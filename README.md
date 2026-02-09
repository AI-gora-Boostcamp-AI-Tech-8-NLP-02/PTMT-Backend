# PTMT Backend

페튜와 매튜(Paper Tutor & Map Tutor) 서비스의 백엔드 FastAPI 서버입니다.

논문(PDF/링크/제목 검색)을 입력받아 학습 커리큘럼 생성을 위한 데이터 파이프라인을 제공합니다.

## 주요 기능

- FastAPI 기반 REST API 제공
- Supabase Auth 기반 회원가입/로그인/토큰 갱신
- 논문 업로드/링크 제출/제목 검색(arXiv) 처리
- Supabase Storage(`papers` 버킷) 업로드 연동
- 커리큘럼 옵션 저장, 생성 요청, 생성 상태/그래프 조회
- 외부 AI API 연동(키워드 추출, 커리큘럼 생성)
- 키 슬롯 대기열(`KeyQueueService`)로 외부 API 호출 제어

## 서비스 아키텍처

<img width="2148" height="1718" alt="architecture" src="https://github.com/user-attachments/assets/40bdb231-ccb0-4419-bbd9-89aaa237a849" />

## 기술 스택

- Python 3.11+
- FastAPI, Uvicorn
- Pydantic v2, SQLModel
- Supabase Python SDK (Auth/PostgREST/Storage)
- httpx, arxiv, grobid-client-python
- pytest, ruff, mypy

## 실행 방법

### 의존성 설치

- Python `3.11` 이상
- `uv` 설치
- Supabase 프로젝트(Auth + Database + Storage)
- (권장) GROBID 서버 (`http://localhost:8070`)

```bash
cp .env.example .env
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 환경 변수 설정

```bash
SUPABASE_URL=https://<your-project-ref>.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
```

### 서버 실행

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

또는

```bash
bash scripts/run_server.sh
```

### API 문서 확인

Swagger: `http://localhost:8000/docs` 에서 확인 가능

### Grobid / 터널 실행 스크립트

이 저장소는 API 서버 코드뿐 아니라 GROBID/터널 실행 스크립트도 함께 관리합니다.

- `scripts/run_server.sh`: FastAPI 개발 서버 실행
- `scripts/test.sh`: 테스트 + 커버리지 실행
- `scripts/grobid_setting.sh`: GROBID 0.8.2 설치/빌드 후 `tmux` 세션(`grobid`)으로 실행
- `scripts/cloudflare_setting.sh`: Cloudflare Tunnel을 `tmux` 세션(`cf-tunnel`)으로 실행

**주의 사항**

- `grobid_setting.sh`, `cloudflare_setting.sh`는 `apt-get`, `sudo`를 사용하므로 Ubuntu/Debian 계열 서버 환경을 전제로 합니다.
- macOS/로컬 개발 환경에서는 `GROBID_COMPLETE_GUIDE.md`의 수동 설치 방법을 사용하는 것을 권장합니다.

## 프로젝트 구조

```bash
PTMT-Backend/
├── app/
│   ├── api/
│   │   ├── routes/              # auth, users, papers, curriculums
│   │   ├── deps.py              # 인증 의존성
│   │   └── router.py            # 라우터 통합
│   ├── core/                    # 설정/보안/에러 처리
│   ├── crud/                    # Supabase CRUD 계층
│   ├── models/                  # SQLModel 모델
│   ├── schemas/                 # 요청/응답 스키마
│   ├── services/                # 도메인 서비스 로직
│   ├── utils/                   # arXiv/GROBID 유틸
│   └── main.py                  # FastAPI 엔트리포인트
├── tests/                       # API/CRUD/Service 테스트
├── scripts/                     # 실행/테스트/운영 스크립트
├── docs/                        # API/RDB 문서
├── .env.example
├── pyproject.toml
└── Dockerfile
```

## 운영 메모

- GROBID 서버가 없으면 PDF 메타데이터 추출은 fallback 데이터로 동작할 수 있습니다.
- 커리큘럼 생성 API 토큰이 없으면 `/generate` 요청은 백그라운드에서 실패 상태로 전환될 수 있습니다.
- Supabase 연결 실패 시 서버는 실행될 수 있지만, 인증/데이터 관련 엔드포인트는 정상 동작하지 않습니다.

## 참고 문서

- API 상세: `docs/API_REFERENCE.md`
- DB 스키마: `docs/RDB_SCHEMA.md`
- GROBID 설정 가이드: `GROBID_COMPLETE_GUIDE.md`  ([Grobid Docs](https://grobid.readthedocs.io/en/latest/))

- 이전 리드미
    
    ```markdown
    # PTMT Backend
    
    PTMT (페튜와 매튜) 서비스의 백엔드 API 서버입니다.  
    논문(PDF/링크/제목 검색)을 입력받아 학습 커리큘럼 생성을 위한 데이터 파이프라인을 제공합니다.
    
    ## 주요 기능
    
    - FastAPI 기반 REST API 제공
    - Supabase Auth 기반 회원가입/로그인/토큰 갱신
    - 논문 업로드/링크 제출/제목 검색(arXiv) 처리
    - Supabase Storage(`papers` 버킷) 업로드 연동
    - 커리큘럼 옵션 저장, 생성 요청, 생성 상태/그래프 조회
    - 외부 AI API 연동(키워드 추출, 커리큘럼 생성)
    - 키 슬롯 대기열(`KeyQueueService`)로 외부 API 호출 제어
    
    ## 기술 스택
    
    - Python 3.11+
    - FastAPI, Uvicorn
    - Pydantic v2, SQLModel
    - Supabase Python SDK (Auth/PostgREST/Storage)
    - httpx, arxiv, grobid-client-python
    - pytest, ruff, mypy
    
    ## 프로젝트 구조
    
    ```text
    PTMT-Backend/
    ├── app/
    │   ├── api/
    │   │   ├── routes/              # auth, users, papers, curriculums
    │   │   ├── deps.py              # 인증 의존성
    │   │   └── router.py            # 라우터 통합
    │   ├── core/                    # 설정/보안/에러 처리
    │   ├── crud/                    # Supabase CRUD 계층
    │   ├── models/                  # SQLModel 모델
    │   ├── schemas/                 # 요청/응답 스키마
    │   ├── services/                # 도메인 서비스 로직
    │   ├── utils/                   # arXiv/GROBID 유틸
    │   └── main.py                  # FastAPI 엔트리포인트
    ├── tests/                       # API/CRUD/Service 테스트
    ├── scripts/                     # 실행/테스트/운영 스크립트
    ├── docs/                        # API/RDB 문서
    ├── .env.example
    ├── pyproject.toml
    └── Dockerfile
    ```
    
    ## 빠른 시작
    
    ### 1) 요구사항
    
    - Python `3.11` 이상
    - `uv` 설치
    - Supabase 프로젝트(Auth + Database + Storage)
    - (권장) GROBID 서버 (`http://localhost:8070`)
    
    ### 2) 설치
    
    ```bash
    cp .env.example .env
    uv venv
    source .venv/bin/activate
    uv pip install -e ".[dev]"
    ```
    
    ### 3) 필수 환경 변수 설정
    
    아래 값이 없으면 인증/CRUD 관련 API가 정상 동작하지 않습니다.
    
    ```env
    SUPABASE_URL=https://<your-project-ref>.supabase.co
    SUPABASE_ANON_KEY=<your-anon-key>
    SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
    ```
    
    ### 4) 서버 실행
    
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    
    또는:
    
    ```bash
    bash scripts/run_server.sh
    ```
    
    ### 5) 확인
    
    - Swagger: `http://localhost:8000/docs`
    - ReDoc: `http://localhost:8000/redoc`
    - Health Check: `http://localhost:8000/health`
    
    ## 스크립트로 운영 관리
    
    이 저장소는 API 서버 코드뿐 아니라 GROBID/터널 실행 스크립트도 함께 관리합니다.
    
    - `scripts/run_server.sh`: FastAPI 개발 서버 실행
    - `scripts/test.sh`: 테스트 + 커버리지 실행
    - `scripts/grobid_setting.sh`: GROBID 0.8.2 설치/빌드 후 `tmux` 세션(`grobid`)으로 실행
    - `scripts/cloudflare_setting.sh`: Cloudflare Tunnel을 `tmux` 세션(`cf-tunnel`)으로 실행
    
    GROBID 자동 설치/실행 예시:
    
    ```bash
    bash scripts/grobid_setting.sh
    tmux attach -t grobid
    ```
    
    Cloudflare Tunnel 실행 예시:
    
    ```bash
    # .env에 TUNNEL_TOKEN 필요
    bash scripts/cloudflare_setting.sh
    tmux attach -t cf-tunnel
    ```
    
    주의:
    
    - `grobid_setting.sh`, `cloudflare_setting.sh`는 `apt-get`, `sudo`를 사용하므로 Ubuntu/Debian 계열 서버 환경을 전제로 합니다.
    - macOS/로컬 개발 환경에서는 `GROBID_COMPLETE_GUIDE.md`의 수동 설치 방법을 사용하는 것을 권장합니다.
    
    ## 환경 변수 가이드
    
    아래는 현재 코드(`app/core/config.py`) 기준 주요 설정입니다.
    
    | 변수명 | 필수 | 설명 | 기본값 |
    |---|---|---|---|
    | `APP_ENV` | 선택 | 실행 환경 (`development`, `production`) | `development` |
    | `DEBUG` | 선택 | 디버그 모드 | `true` |
    | `HOST` | 선택 | 서버 바인딩 호스트 | `0.0.0.0` |
    | `PORT` | 선택 | 서버 포트 | `8000` |
    | `CORS_ORIGINS` | 권장 | 허용 origin 목록(쉼표 구분) | `http://localhost:3000,...` |
    | `SUPABASE_URL` | 필수 | Supabase 프로젝트 URL | 없음 |
    | `SUPABASE_ANON_KEY` | 필수(Auth) | Supabase Auth/sign-in 및 토큰 검증용 | 없음 |
    | `SUPABASE_SERVICE_ROLE_KEY` | 필수(CRUD/Storage) | 서버 사이드 DB/Storage 접근용 | 없음 |
    | `MAX_UPLOAD_SIZE_MB` | 선택 | PDF 최대 업로드 크기(MB) | `25` |
    | `STORAGE_PATH` | 선택 | 로컬 스토리지 경로(일부 fallback) | `./storage` |
    | `AUTH_REFRESH_COOKIE_NAME` | 선택 | Refresh Cookie 이름 | `ptmt_refresh_token` |
    | `AUTH_REFRESH_COOKIE_PATH` | 선택 | Refresh Cookie Path | `/api/auth` |
    | `AUTH_REFRESH_COOKIE_SAMESITE` | 선택 | Refresh Cookie SameSite | `lax` |
    | `AUTH_REFRESH_COOKIE_SECURE` | 선택 | HTTPS only cookie 여부 | `false` |
    | `AUTH_REFRESH_COOKIE_DOMAIN` | 선택 | Cookie Domain | 없음 |
    | `CURRICULUM_GENERATION_API_URL` | 선택 | 외부 커리큘럼 생성 API URL | `http://curr.ptmt.site` |
    | `CURRICULUM_GENERATION_API_TOKEN` | 생성 시 사실상 필수 | 커리큘럼 생성 API Bearer 토큰 | 빈 값 |
    | `KEYWORD_EXTRACTION_API_URL` | 선택 | 외부 키워드 추출 API URL | `http://curr.ptmt.site` |
    | `KEYWORD_EXTRACTION_API_TOKEN` | 선택 | 키워드 추출 API Bearer 토큰 | 빈 값 |
    | `KEY_QUEUE_TOTAL_KEYS` | 선택 | 동시 키 슬롯 수 | `5` |
    | `KEY_QUEUE_COOLDOWN_SECONDS` | 선택 | 기본 쿨다운(초) | `30` |
    | `KEY_QUEUE_CURRICULUM_COOLDOWN_SECONDS` | 선택 | 커리큘럼 생성 쿨다운(초) | `60` |
    | `KEY_QUEUE_MAX_BUSY_SECONDS` | 선택 | 슬롯 점유 최대 시간(초) | `600` |
    | `TUNNEL_TOKEN` | 선택(스크립트용) | `scripts/cloudflare_setting.sh`에서 Cloudflare Tunnel 실행 시 사용 | 빈 값 |
    
    참고:
    
    -  현재 인증 핵심 경로는 Supabase Auth 기반입니다.
    - `papers` Storage 버킷이 없으면 `/api/papers/pdf` 처리 시 실패할 수 있습니다.
    
    ## 인증 방식
    
    1. 로그인/회원가입 성공 시 응답 JSON에 `access_token`이 포함되고, refresh token은 `HttpOnly` 쿠키로 설정됩니다.
    2. 보호된 API 호출 시 `Authorization: Bearer <access_token>` 헤더가 필요합니다.
    3. 브라우저에서 `/api/auth/refresh`, `/api/auth/logout` 호출 시 `credentials: "include"`를 사용해야 합니다.
    
    ## API 요약
    
    Base URL: `http://localhost:8000/api`
    
    ### Auth
    
    - `POST /auth/signup`
    - `POST /auth/login`
    - `POST /auth/logout`
    - `POST /auth/refresh`
    
    ### Users
    
    - `GET /users/me`
    - `PATCH /users/me`
    
    ### Papers
    
    - `GET /papers`
    - `GET /papers/{paper_id}`
    - `DELETE /papers/{paper_id}`
    - `POST /papers/pdf`
    - `POST /papers/link`
    - `POST /papers/search`
    
    ### Curriculums
    
    - `GET /curriculums`
    - `GET /curriculums/queue-status`
    - `GET /curriculums/{curriculum_id}`
    - `DELETE /curriculums/{curriculum_id}`
    - `POST /curriculums/{curriculum_id}/options`
    - `POST /curriculums/{curriculum_id}/generate`
    - `GET /curriculums/{curriculum_id}/status`
    - `GET /curriculums/{curriculum_id}/graph`
    - `POST /curriculums/import`
    - `POST /curriculums/import_failed`
    
    ## 권장 사용 플로우
    
    1. `POST /api/papers/pdf` 또는 `POST /api/papers/link` 또는 `POST /api/papers/search`
    2. 응답의 `curriculum_id` 확보
    3. `POST /api/curriculums/{curriculum_id}/options`
    4. `POST /api/curriculums/{curriculum_id}/generate`
    5. `GET /api/curriculums/{curriculum_id}/status` 폴링
    6. 필요 시 `GET /api/curriculums/queue-status`로 대기열 상태 확인
    7. 완료 후 `GET /api/curriculums/{curriculum_id}/graph` 조회
    
    ## 테스트/품질 체크
    
    ```bash
    # 전체 테스트
    pytest
    
    # 커버리지 포함 테스트
    bash scripts/test.sh
    
    # 린트
    ruff check .
    
    # 타입체크
    mypy app
    ```
    
    ## 운영 메모
    
    - GROBID 서버가 없으면 PDF 메타데이터 추출은 fallback 데이터로 동작할 수 있습니다.
    - 커리큘럼 생성 API 토큰이 없으면 `/generate` 요청은 백그라운드에서 실패 상태로 전환될 수 있습니다.
    - Supabase 연결 실패 시 서버는 실행될 수 있지만, 인증/데이터 관련 엔드포인트는 정상 동작하지 않습니다.
    
    ## 참고 문서
    
    - API 상세: `docs/API_REFERENCE.md`
    - DB 스키마: `docs/RDB_SCHEMA.md`
    - GROBID 설정 가이드: `GROBID_COMPLETE_GUIDE.md`
    
    ```
