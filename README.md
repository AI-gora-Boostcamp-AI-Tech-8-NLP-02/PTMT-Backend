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
