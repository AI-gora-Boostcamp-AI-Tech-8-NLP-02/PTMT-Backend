# PTMT Backend API Reference

> Base URL: `http://localhost:8000/api`

## 공통 사항

### 응답 형식

모든 API는 표준 응답 형식을 따릅니다:

```json
// 성공 응답
{
  "success": true,
  "data": { ... }
}

// 에러 응답
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지",
    "details": {}
  }
}
```

### 공통 Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Content-Type` | `application/json` | O | JSON 요청 시 필수 |
| `Authorization` | `Bearer {token}` | 조건부 | 인증 필요 API에서 필수 |
| `Accept` | `application/json` | - | 응답 형식 지정 (선택) |

---

## 1. Auth API

### POST `/auth/signup`

회원가입

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Content-Type` | `application/json` | O | JSON 형식 명시 |

#### Request Body

```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "홍길동"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | O | 이메일 주소 (유효한 이메일 형식) |
| `password` | string | O | 비밀번호 (최소 8자) |
| `name` | string | O | 사용자 이름 |

#### Response (201 Created)

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user-xxx",
      "email": "user@example.com",
      "name": "홍길동",
      "role": "user",
      "avatar_url": null,
      "created_at": "2024-01-25T00:00:00Z",
      "stats": {
        "total_curriculums": 0,
        "completed_curriculums": 0,
        "total_study_hours": 0
      }
    },
    "access_token": "eyJhbG...",
    "refresh_token": "eyJhbG...",
    "expires_in": 3600
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `user` | object | 생성된 사용자 정보 |
| `user.id` | string | 사용자 고유 ID |
| `user.email` | string | 이메일 주소 |
| `user.name` | string | 사용자 이름 |
| `user.role` | string | 사용자 역할 (user, admin) |
| `user.avatar_url` | string \| null | 프로필 이미지 URL |
| `user.created_at` | string | 가입일시 (ISO 8601) |
| `user.stats` | object | 사용자 통계 정보 |
| `user.stats.total_curriculums` | number | 생성한 커리큘럼 총 개수 |
| `user.stats.completed_curriculums` | number | 완료한 커리큘럼 개수 |
| `user.stats.total_study_hours` | number | 총 학습 시간 (시간 단위) |
| `access_token` | string | JWT 액세스 토큰 (API 호출용) |
| `refresh_token` | string | JWT 리프레시 토큰 (토큰 갱신용) |
| `expires_in` | number | 액세스 토큰 만료 시간 (초) |

---

### POST `/auth/login`

로그인

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Content-Type` | `application/json` | O | JSON 형식 명시 |

#### Request Body

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | O | 가입된 이메일 주소 |
| `password` | string | O | 비밀번호 |

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user-xxx",
      "email": "user@example.com",
      "name": "홍길동",
      "role": "user",
      "avatar_url": null,
      "created_at": "2024-01-25T00:00:00Z",
      "stats": {
        "total_curriculums": 5,
        "completed_curriculums": 3,
        "total_study_hours": 24.5
      }
    },
    "access_token": "eyJhbG...",
    "refresh_token": "eyJhbG...",
    "expires_in": 3600
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `user` | object | 사용자 정보 |
| `user.id` | string | 사용자 고유 ID |
| `user.email` | string | 이메일 주소 |
| `user.name` | string | 사용자 이름 |
| `user.role` | string | 사용자 역할 (user, admin) |
| `user.avatar_url` | string \| null | 프로필 이미지 URL |
| `user.created_at` | string | 가입일시 (ISO 8601) |
| `user.stats` | object | 사용자 통계 정보 |
| `access_token` | string | JWT 액세스 토큰 |
| `refresh_token` | string | JWT 리프레시 토큰 |
| `expires_in` | number | 토큰 만료 시간 (초) |

---

### POST `/auth/logout`

로그아웃 - 현재 세션을 종료하고 refresh_token을 무효화합니다.

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Authorization` | `Bearer {access_token}` | O | 로그아웃할 사용자의 액세스 토큰 |

#### Request Body

없음 (헤더의 토큰으로 사용자 식별)

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "message": "로그아웃 되었습니다."
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | 처리 결과 메시지 |

---

### POST `/auth/refresh`

토큰 갱신 - 만료된 access_token을 새로 발급받습니다.

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Content-Type` | `application/json` | O | JSON 형식 명시 |

#### Request Body

```json
{
  "refresh_token": "eyJhbG..."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refresh_token` | string | O | 로그인 시 받은 리프레시 토큰 |

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbG...",
    "expires_in": 3600
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | 새로 발급된 액세스 토큰 |
| `expires_in` | number | 토큰 만료 시간 (초) |

---

## 2. Users API

### GET `/users/me`

내 프로필 조회 - 현재 로그인한 사용자의 정보를 조회합니다.

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Authorization` | `Bearer {access_token}` | O | 액세스 토큰 |

#### Request Body

없음

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "id": "user-xxx",
    "email": "user@example.com",
    "name": "홍길동",
    "role": "user",
    "avatar_url": null,
    "created_at": "2024-01-25T00:00:00Z",
    "stats": {
      "total_curriculums": 5,
      "completed_curriculums": 3,
      "total_study_hours": 24.5
    }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | 사용자 고유 ID |
| `email` | string | 이메일 주소 |
| `name` | string | 사용자 이름 |
| `role` | string | 사용자 역할 |
| `avatar_url` | string \| null | 프로필 이미지 URL |
| `created_at` | string | 가입일시 (ISO 8601) |
| `stats.total_curriculums` | number | 생성한 커리큘럼 수 |
| `stats.completed_curriculums` | number | 완료한 커리큘럼 수 |
| `stats.total_study_hours` | number | 총 학습 시간 |

---

### PATCH `/users/me`

프로필 수정 - 사용자 정보를 업데이트합니다.

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Authorization` | `Bearer {access_token}` | O | 액세스 토큰 |
| `Content-Type` | `application/json` | O | JSON 형식 명시 |

#### Request Body

```json
{
  "name": "새 이름",
  "avatar_url": "https://example.com/avatar.png"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | - | 변경할 이름 |
| `avatar_url` | string \| null | - | 변경할 프로필 이미지 URL |

> 변경하지 않을 필드는 생략 가능합니다.

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "id": "user-xxx",
    "email": "user@example.com",
    "name": "새 이름",
    "role": "user",
    "avatar_url": "https://example.com/avatar.png",
    "created_at": "2024-01-25T00:00:00Z",
    "stats": {
      "total_curriculums": 5,
      "completed_curriculums": 3,
      "total_study_hours": 24.5
    }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | 사용자 고유 ID |
| `email` | string | 이메일 주소 |
| `name` | string | 수정된 사용자 이름 |
| `role` | string | 사용자 역할 |
| `avatar_url` | string \| null | 수정된 프로필 이미지 URL |
| `created_at` | string | 가입일시 (ISO 8601) |
| `stats` | object | 사용자 통계 정보 |

---

## 3. Papers API

### POST `/papers/pdf`

PDF 파일 업로드 - PDF 논문을 업로드하고 AI가 분석합니다.

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Authorization` | `Bearer {access_token}` | O | 액세스 토큰 |
| `Content-Type` | `multipart/form-data` | O | 파일 업로드 형식 |

#### Request Body (Form Data)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | O | PDF 파일 (최대 25MB) |

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "paper_id": "paper-xxx",
    "curriculum_id": "curr-xxx",
    "title": "Attention Is All You Need",
    "authors": ["Vaswani", "Shazeer", "Parmar"],
    "abstract": "The dominant sequence transduction models...",
    "language": "english",
    "keywords": [
      { "name": "Transformer" },
      { "name": "Attention" },
      { "name": "Self-Attention" },
      { "name": "Encoder-Decoder" }
    ],
    "source_url": null,
    "pdf_url": "https://storage.example.com/papers/xxx.pdf"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `paper_id` | string | 생성된 논문 ID |
| `curriculum_id` | string | 자동 생성된 커리큘럼 ID (draft 상태) |
| `title` | string | AI가 추출한 논문 제목 |
| `authors` | string[] | 저자 목록 |
| `abstract` | string | 논문 초록/요약 |
| `language` | string | 논문 언어 (english, korean 등) |
| `keywords` | Keyword[] | AI가 1차 추출한 키워드 목록 |
| `keywords[].name` | string | 키워드 이름 |
| `source_url` | string \| null | 원본 URL (링크 제출 시) |
| `pdf_url` | string \| null | 저장된 PDF URL |

> **Note:** 1차 키워드 추출 단계에서는 `name`만 반환됩니다. `id`, `importance` 등 상세 정보는 커리큘럼 생성 후 그래프 조회 시 확인할 수 있습니다.

---

### POST `/papers/link`

논문 링크 제출 - URL로 논문을 분석합니다.

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Authorization` | `Bearer {access_token}` | O | 액세스 토큰 |
| `Content-Type` | `application/json` | O | JSON 형식 명시 |

#### Request Body

```json
{
  "url": "https://arxiv.org/abs/1706.03762"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | O | 논문 URL (arXiv, Semantic Scholar 등) |

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "paper_id": "paper-xxx",
    "curriculum_id": "curr-xxx",
    "title": "Attention Is All You Need",
    "authors": ["Vaswani", "Shazeer", "Parmar"],
    "abstract": "The dominant sequence transduction models...",
    "language": "english",
    "keywords": [
      { "name": "Transformer" },
      { "name": "Attention" },
      { "name": "Self-Attention" }
    ],
    "source_url": "https://arxiv.org/abs/1706.03762",
    "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf"
  }
}
```

---

### POST `/papers/search`

논문 제목 검색 - 제목으로 논문을 검색하고 분석합니다.

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Authorization` | `Bearer {access_token}` | O | 액세스 토큰 |
| `Content-Type` | `application/json` | O | JSON 형식 명시 |

#### Request Body

```json
{
  "title": "Attention Is All You Need"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | O | 검색할 논문 제목 |

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "paper_id": "paper-xxx",
    "curriculum_id": "curr-xxx",
    "title": "Attention Is All You Need",
    "authors": ["Vaswani", "Shazeer", "Parmar"],
    "abstract": "The dominant sequence transduction models...",
    "language": "english",
    "keywords": [
      { "name": "Transformer" },
      { "name": "Attention" },
      { "name": "Self-Attention" }
    ],
    "source_url": null,
    "pdf_url": null
  }
}
```

---

## 4. Curriculums API

### GET `/curriculums`

커리큘럼 목록 조회 - 내가 생성한 커리큘럼 목록을 조회합니다.

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Authorization` | `Bearer {access_token}` | O | 액세스 토큰 |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | string | - | - | 상태 필터 (draft, options_saved, generating, ready, failed) |
| `page` | number | - | 1 | 페이지 번호 |
| `limit` | number | - | 10 | 페이지당 항목 수 (1-100) |

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "curr-1",
        "title": "NLP 트랜스포머 입문",
        "paper_title": "Attention Is All You Need",
        "status": "ready",
        "created_at": "2024-01-20T10:30:00Z",
        "updated_at": "2024-01-20T12:00:00Z",
        "node_count": 16,
        "estimated_hours": 24
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 5,
      "has_more": false
    }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `items` | CurriculumListItem[] | 커리큘럼 목록 |
| `items[].id` | string | 커리큘럼 ID |
| `items[].title` | string | 커리큘럼 제목 |
| `items[].paper_title` | string | 원본 논문 제목 |
| `items[].status` | string | 상태 (아래 Enum 참조) |
| `items[].created_at` | string | 생성일시 (ISO 8601) |
| `items[].updated_at` | string | 수정일시 (ISO 8601) |
| `items[].node_count` | number | 학습 노드 개수 |
| `items[].estimated_hours` | number | 예상 학습 시간 (시간) |
| `pagination.page` | number | 현재 페이지 |
| `pagination.limit` | number | 페이지당 항목 수 |
| `pagination.total` | number | 전체 항목 수 |
| `pagination.has_more` | boolean | 다음 페이지 존재 여부 |

**CurriculumStatus Enum:**

| Value | Description |
|-------|-------------|
| `draft` | 초안 (논문 업로드 완료) |
| `options_saved` | 옵션 설정 완료 |
| `generating` | AI 생성 중 |
| `ready` | 생성 완료 (학습 가능) |
| `failed` | 생성 실패 |

---

### GET `/curriculums/{curriculum_id}`

커리큘럼 단일 조회 - 커리큘럼 상세 정보를 조회합니다.

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Authorization` | `Bearer {access_token}` | O | 액세스 토큰 |

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `curriculum_id` | string | O | 조회할 커리큘럼 ID |

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "id": "curr-1",
    "title": "NLP 트랜스포머 입문",
    "status": "ready",
    "purpose": "deep_research",
    "level": "master",
    "budgeted_time": { "days": 14, "daily_hours": 2 },
    "preferred_resources": ["paper", "article"],
    "paper": {
      "id": "paper-1",
      "title": "Attention Is All You Need",
      "authors": ["Vaswani et al."],
      "abstract": "The dominant sequence transduction models..."
    },
    "created_at": "2024-01-20T10:30:00Z",
    "updated_at": "2024-01-20T12:00:00Z"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | 커리큘럼 ID |
| `title` | string | 커리큘럼 제목 |
| `status` | string | 상태 |
| `purpose` | string | 학습 목적 (아래 Enum 참조) |
| `level` | string | 사용자 수준 (아래 Enum 참조) |
| `budgeted_time.days` | number | 학습 기간 (일) |
| `budgeted_time.daily_hours` | number | 일일 학습 시간 (시간) |
| `preferred_resources` | string[] | 선호 리소스 타입 |
| `paper.id` | string | 원본 논문 ID |
| `paper.title` | string | 논문 제목 |
| `paper.authors` | string[] | 저자 목록 |
| `paper.abstract` | string | 논문 초록 |

---

### DELETE `/curriculums/{curriculum_id}`

커리큘럼 삭제

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Authorization` | `Bearer {access_token}` | O | 액세스 토큰 |

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `curriculum_id` | string | O | 삭제할 커리큘럼 ID |

#### Request Body

없음

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "message": "커리큘럼이 삭제되었습니다."
  }
}
```

---

### POST `/curriculums/{curriculum_id}/options`

커리큘럼 옵션 저장 - 학습 목적, 수준, 시간 등을 설정합니다.

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Authorization` | `Bearer {access_token}` | O | 액세스 토큰 |
| `Content-Type` | `application/json` | O | JSON 형식 명시 |

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `curriculum_id` | string | O | 커리큘럼 ID |

#### Request Body

```json
{
  "purpose": "deep_research",
  "level": "master",
  "known_concepts": ["kw-1", "kw-2"],
  "budgeted_time": {
    "days": 14,
    "daily_hours": 2
  },
  "preferred_resources": ["paper", "article", "video"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `purpose` | string | O | 학습 목적 (아래 Enum 참조) |
| `level` | string | O | 현재 수준 (아래 Enum 참조) |
| `known_concepts` | string[] | O | 이미 아는 키워드 ID 목록 |
| `budgeted_time.days` | number | O | 학습 기간 (일) |
| `budgeted_time.daily_hours` | number | O | 일일 학습 시간 |
| `preferred_resources` | string[] | O | 선호 리소스 타입 목록 |

**CurriculumPurpose Enum:**

| Value | Description |
|-------|-------------|
| `deep_research` | 심층 연구 |
| `simple_study` | 개념 학습 |
| `trend_check` | 트렌드 파악 |
| `code_implementation` | 구현 실습 |
| `exam_preparation` | 시험 준비 |

**UserLevel Enum:**

| Value | Description |
|-------|-------------|
| `non_major` | 입문자 (비전공) |
| `bachelor` | 학부생 |
| `master` | 대학원생 |
| `researcher` | 연구원 |
| `industry` | 현업 종사자 |

**ResourceType Enum:**

| Value | Description |
|-------|-------------|
| `paper` | 원문 논문 |
| `article` | 블로그/아티클 |
| `video` | 영상 강의 |
| `code` | 코드/튜토리얼 |

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "curriculum_id": "curr-xxx",
    "status": "options_saved"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `curriculum_id` | string | 커리큘럼 ID |
| `status` | string | 변경된 상태 (options_saved) |

---

### POST `/curriculums/{curriculum_id}/generate`

커리큘럼 생성 시작 - AI가 학습 경로를 생성합니다. (비동기)

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Authorization` | `Bearer {access_token}` | O | 액세스 토큰 |

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `curriculum_id` | string | O | 커리큘럼 ID |

#### Request Body

없음

#### Response (202 Accepted)

```json
{
  "success": true,
  "data": {
    "curriculum_id": "curr-xxx",
    "status": "generating"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `curriculum_id` | string | 커리큘럼 ID |
| `status` | string | 상태 (generating) |

---

### GET `/curriculums/{curriculum_id}/status`

생성 상태 확인 - 커리큘럼 생성 진행률을 확인합니다. (폴링용)

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Authorization` | `Bearer {access_token}` | O | 액세스 토큰 |

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `curriculum_id` | string | O | 커리큘럼 ID |

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "curriculum_id": "curr-xxx",
    "status": "generating",
    "progress_percent": 75,
    "current_step": "키워드 분석 중..."
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `curriculum_id` | string | 커리큘럼 ID |
| `status` | string | 현재 상태 |
| `progress_percent` | number | 진행률 (0-100) |
| `current_step` | string | 현재 작업 단계 설명 |

---

### GET `/curriculums/{curriculum_id}/graph`

커리큘럼 그래프 조회 - 학습 노드와 연결 관계를 조회합니다.

#### Headers

| Key | Value | Required | Description |
|-----|-------|----------|-------------|
| `Authorization` | `Bearer {access_token}` | O | 액세스 토큰 |

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `curriculum_id` | string | O | 커리큘럼 ID |

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "meta": {
      "curriculum_id": "curr-xxx",
      "paper_id": "paper-xxx",
      "paper_title": "Attention Is All You Need",
      "paper_authors": ["Vaswani et al."],
      "created_at": "2024-01-20T10:30:00Z",
      "total_study_time_hours": 24.5,
      "total_nodes": 16
    },
    "nodes": [
      {
        "keyword_id": "node-1",
        "keyword": "Transformer",
        "description": "Self-Attention 기반 시퀀스 모델",
        "importance": 10,
        "layer": 5,
        "resources": [
          {
            "resource_id": "res-1",
            "name": "The Illustrated Transformer",
            "url": "https://jalammar.github.io/illustrated-transformer/",
            "type": "article",
            "description": "트랜스포머 아키텍처 시각화 설명",
            "difficulty": 5,
            "importance": 9,
            "study_load_minutes": 60,
            "is_core": true
          }
        ]
      }
    ],
    "edges": [
      {
        "from_keyword_id": "node-1",
        "to_keyword_id": "node-2",
        "relationship": "prerequisite"
      }
    ]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| **meta** | object | 그래프 메타 정보 |
| `meta.curriculum_id` | string | 커리큘럼 ID |
| `meta.paper_id` | string | 원본 논문 ID |
| `meta.paper_title` | string | 논문 제목 |
| `meta.paper_authors` | string[] | 저자 목록 |
| `meta.created_at` | string | 생성일시 |
| `meta.total_study_time_hours` | number | 총 예상 학습 시간 |
| `meta.total_nodes` | number | 총 노드 개수 |
| **nodes** | Node[] | 학습 노드 목록 |
| `nodes[].keyword_id` | string | 노드(키워드) ID |
| `nodes[].keyword` | string | 키워드 이름 |
| `nodes[].description` | string | 키워드 설명 |
| `nodes[].importance` | number | 중요도 (1-10) |
| `nodes[].layer` | number | 그래프 레이어 (학습 순서) |
| `nodes[].resources` | Resource[] | 학습 리소스 목록 |
| **resources[]** | object | 리소스 정보 |
| `resources[].resource_id` | string | 리소스 ID |
| `resources[].name` | string | 리소스 이름 |
| `resources[].url` | string | 리소스 URL |
| `resources[].type` | string | 리소스 타입 (paper, article, video, code) |
| `resources[].description` | string | 리소스 설명 |
| `resources[].difficulty` | number | 난이도 (1-10) |
| `resources[].importance` | number | 중요도 (1-10) |
| `resources[].study_load_minutes` | number | 예상 학습 시간 (분) |
| `resources[].is_core` | boolean | 핵심 리소스 여부 |
| **edges** | Edge[] | 노드 연결 관계 |
| `edges[].from_keyword_id` | string | 시작 노드 ID |
| `edges[].to_keyword_id` | string | 도착 노드 ID |
| `edges[].relationship` | string | 관계 타입 (prerequisite: 선수 지식) |

---

## 에러 코드

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | 인증 필요 (토큰 없음) |
| `INVALID_TOKEN` | 401 | 유효하지 않은 토큰 |
| `TOKEN_EXPIRED` | 401 | 만료된 토큰 |
| `INVALID_CREDENTIALS` | 401 | 이메일/비밀번호 불일치 |
| `FORBIDDEN` | 403 | 권한 없음 (다른 사용자 리소스 접근) |
| `USER_NOT_FOUND` | 404 | 사용자 없음 |
| `PAPER_NOT_FOUND` | 404 | 논문 없음 |
| `CURRICULUM_NOT_FOUND` | 404 | 커리큘럼 없음 |
| `PAPER_SEARCH_NOT_FOUND` | 404 | 검색 결과 없음 |
| `CURRICULUM_NOT_READY` | 400 | 커리큘럼 생성 중 (그래프 조회 불가) |
| `EMAIL_ALREADY_EXISTS` | 409 | 이메일 중복 |
| `INVALID_PDF` | 400 | PDF 형식 오류 |
| `FILE_TOO_LARGE` | 413 | 파일 크기 초과 (25MB) |
| `INVALID_URL` | 400 | 잘못된 URL 형식 |
| `GENERATION_FAILED` | 500 | 커리큘럼 생성 실패 |
| `RATE_LIMIT_EXCEEDED` | 429 | 요청 횟수 초과 |
| `INTERNAL_SERVER_ERROR` | 500 | 서버 내부 오류 |

---

## API 요약

| Category | Method | Endpoint | Auth | Description |
|----------|--------|----------|------|-------------|
| Auth | POST | `/auth/signup` | - | 회원가입 |
| Auth | POST | `/auth/login` | - | 로그인 |
| Auth | POST | `/auth/logout` | O | 로그아웃 |
| Auth | POST | `/auth/refresh` | - | 토큰 갱신 |
| Users | GET | `/users/me` | O | 프로필 조회 |
| Users | PATCH | `/users/me` | O | 프로필 수정 |
| Papers | POST | `/papers/pdf` | O | PDF 업로드 |
| Papers | POST | `/papers/link` | O | 링크 제출 |
| Papers | POST | `/papers/search` | O | 제목 검색 |
| Curriculums | GET | `/curriculums` | O | 목록 조회 |
| Curriculums | GET | `/curriculums/{id}` | O | 단일 조회 |
| Curriculums | DELETE | `/curriculums/{id}` | O | 삭제 |
| Curriculums | POST | `/curriculums/{id}/options` | O | 옵션 저장 |
| Curriculums | POST | `/curriculums/{id}/generate` | O | 생성 시작 |
| Curriculums | GET | `/curriculums/{id}/status` | O | 상태 확인 |
| Curriculums | GET | `/curriculums/{id}/graph` | O | 그래프 조회 |

**Total: 16 Endpoints**
