# PTMT Backend

**PTMT (페튜와 매튜)** - 논문 기반 맞춤형 커리큘럼 생성 서비스 백엔드

## 기술 스택

- **Framework**: FastAPI
- **Database**: PostgreSQL (Supabase)
- **ORM**: SQLModel
- **Auth**: JWT (python-jose)
- **Package Manager**: uv

## 프로젝트 구조

```
backend/
├── alembic/                # DB 마이그레이션
│   ├── versions/           # 마이그레이션 스크립트
│   └── env.py              # Alembic 설정
├── app/
│   ├── api/v1/
│   │   ├── routes/
│   │   │   ├── auth.py         # 인증 API
│   │   │   ├── users.py        # 사용자 API
│   │   │   ├── papers.py       # 논문 API
│   │   │   └── curriculums.py  # 커리큘럼 + Progress API
│   │   ├── deps.py             # 의존성 주입
│   │   └── router.py           # 라우터 통합
│   ├── core/
│   │   ├── config.py           # 환경 변수 설정
│   │   └── security.py         # JWT, 비밀번호 해싱
│   ├── models/                 # SQLModel 정의
│   ├── schemas/                # Pydantic 스키마
│   ├── services/               # 비즈니스 로직
│   ├── crud/                   # DB CRUD 작업
│   └── main.py                 # FastAPI 앱 엔트리포인트
├── scripts/
│   ├── prestart.sh             # 서버 시작 전 스크립트
│   └── test.sh                 # 테스트 실행 스크립트
├── tests/                      # 테스트 코드
├── storage/                    # 업로드 파일 임시 저장
├── .env.example                # 환경 변수 템플릿
├── alembic.ini                 # Alembic 설정
├── Dockerfile                  # Docker 이미지 빌드
└── pyproject.toml              # 패키지 및 프로젝트 설정
```

## 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
cd PTMT-Backend

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 필요한 값 설정
```

### 2. 의존성 설치

```bash
# uv 사용 (권장)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# 또는 pip 사용
pip install -e ".[dev]"
```

### 3. 서버 실행

```bash
# 개발 모드 (자동 리로드)
uvicorn app.main:app --reload --port 8000

# 또는
python -m app.main
```

### 4. API 문서 확인

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `APP_ENV` | 환경 (development/production) | development |
| `DEBUG` | 디버그 모드 | true |
| `DATABASE_URL` | PostgreSQL 연결 URL | - |
| `JWT_SECRET_KEY` | JWT 서명 키 | - |
| `JWT_ALGORITHM` | JWT 알고리즘 | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 액세스 토큰 만료 시간 | 60 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 리프레시 토큰 만료 일수 | 7 |
| `CORS_ORIGINS` | 허용된 CORS 출처 | http://localhost:3000 |

## API 엔드포인트

### Auth (`/api/auth`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/signup` | 회원가입 |
| POST | `/login` | 로그인 |
| POST | `/logout` | 로그아웃 |
| POST | `/refresh` | 토큰 갱신 |

### Users (`/api/users`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/me` | 내 프로필 조회 |
| PATCH | `/me` | 프로필 수정 |

### Papers (`/api/papers`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/pdf` | PDF 업로드 |
| POST | `/link` | 링크 제출 |
| POST | `/search` | 제목 검색 |

### Curriculums (`/api/curriculums`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/` | 목록 조회 |
| GET | `/{id}` | 단일 조회 |
| DELETE | `/{id}` | 삭제 |
| POST | `/{id}/options` | 옵션 저장 |
| POST | `/{id}/generate` | 생성 시작 |
| GET | `/{id}/status` | 생성 상태 확인 |
| GET | `/{id}/graph` | 그래프 조회 |
| GET | `/{id}/progress` | 학습 진행 조회 |
| PATCH | `/{id}/progress` | 학습 진행 업데이트 |

## 데이터베이스

### Supabase 연결

```bash
# .env 파일에 설정
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
```

### 마이그레이션

```bash
# 새 마이그레이션 생성
alembic revision --autogenerate -m "description"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1
```

## 테스트

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov=app --cov-report=html

# 특정 테스트 실행
pytest tests/api/test_auth.py -v
```

## Docker

```bash
# 이미지 빌드
docker build -t ptmt-backend .

# 컨테이너 실행
docker run -p 8000:8000 --env-file .env ptmt-backend
```

## 개발 가이드

### 코드 스타일

```bash
# 린트 검사
ruff check .

# 자동 수정
ruff check --fix .

# 타입 검사
mypy app
```

### 새 API 추가

1. `app/schemas/`에 요청/응답 스키마 정의
2. `app/api/v1/routes/`에 라우터 추가
3. `app/api/v1/router.py`에 라우터 등록
4. 테스트 작성

### 응답 형식

모든 API는 표준 응답 형식을 따릅니다:

```json
// 성공
{
  "success": true,
  "data": { ... }
}

// 실패
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지"
  }
}
```

## TODO

현재 더미 데이터로 구현되어 있습니다. 실제 구현이 필요한 항목:

- [ ] Supabase DB 연결 및 CRUD 구현
- [ ] 실제 인증 로직 (비밀번호 검증, 토큰 저장)
- [ ] PDF 텍스트 추출 서비스
- [ ] AI 기반 커리큘럼 생성 로직
- [ ] 외부 논문 검색 API 연동 (arXiv, Semantic Scholar)
- [ ] Supabase Storage 연동 (PDF 저장)
- [ ] 비밀번호 재설정 API

## 라이선스

MIT License
