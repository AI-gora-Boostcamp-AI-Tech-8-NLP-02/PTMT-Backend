# PTMT RDB 스키마 설계

> Supabase PostgreSQL 기준

## ERD

```
┌─────────────────┐       ┌─────────────────┐
│     users       │       │  refresh_tokens │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │◄──────┤ user_id (FK)    │
│ email           │       │ id (PK)         │
│ password_hash   │       │ token_hash      │
│ name            │       │ expires_at      │
│ avatar_url      │       │ revoked_at      │
│ role            │       │ created_at      │
│ created_at      │       └─────────────────┘
│ updated_at      │
└────────┬────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│     papers      │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ title           │
│ authors[]       │
│ abstract        │
│ language        │
│ source_url      │
│ pdf_storage_path│
│ created_at      │
└────────┬────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│   curriculums   │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ paper_id (FK)   │
│ title           │
│ status          │
│ purpose         │
│ level           │
│ known_concepts[]│
│ budgeted_time   │
│ preferred_res[] │
│ graph_data (JSON)│◄── nodes, edges, resources 통합
│ node_count      │
│ estimated_hours │
│ created_at      │
│ updated_at      │
└─────────────────┘
```

---

## 테이블 정의

### 1. users

사용자 정보

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | gen_random_uuid() | PK |
| `email` | VARCHAR(255) | NO | - | 이메일 (UNIQUE) |
| `password_hash` | VARCHAR(255) | NO | - | 해시된 비밀번호 |
| `name` | VARCHAR(100) | NO | - | 사용자 이름 |
| `avatar_url` | TEXT | YES | NULL | 프로필 이미지 URL |
| `role` | VARCHAR(20) | NO | 'user' | 역할 (user, admin) |
| `created_at` | TIMESTAMP | NO | NOW() | 생성일시 |
| `updated_at` | TIMESTAMP | NO | NOW() | 수정일시 |

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

---

### 2. refresh_tokens

JWT 리프레시 토큰 관리

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | gen_random_uuid() | PK |
| `user_id` | UUID | NO | - | FK → users.id |
| `token_hash` | VARCHAR(255) | NO | - | 해시된 토큰 |
| `expires_at` | TIMESTAMP | NO | - | 만료일시 |
| `created_at` | TIMESTAMP | NO | NOW() | 생성일시 |
| `revoked_at` | TIMESTAMP | YES | NULL | 취소일시 (로그아웃) |

```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMP
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
```

---

### 3. papers

업로드된 논문 정보

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | gen_random_uuid() | PK |
| `user_id` | UUID | NO | - | FK → users.id |
| `title` | VARCHAR(500) | NO | - | 논문 제목 |
| `authors` | TEXT[] | YES | NULL | 저자 목록 |
| `abstract` | TEXT | YES | NULL | 초록 |
| `language` | VARCHAR(20) | NO | 'english' | 언어 |
| `source_url` | TEXT | YES | NULL | 원본 URL |
| `pdf_storage_path` | TEXT | YES | NULL | Storage 경로 |
| `created_at` | TIMESTAMP | NO | NOW() | 생성일시 |

```sql
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    authors TEXT[],
    abstract TEXT,
    language VARCHAR(20) NOT NULL DEFAULT 'english',
    source_url TEXT,
    pdf_storage_path TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_papers_user_id ON papers(user_id);
```

---

### 4. curriculums

커리큘럼 및 그래프 데이터

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | gen_random_uuid() | PK |
| `user_id` | UUID | NO | - | FK → users.id |
| `paper_id` | UUID | NO | - | FK → papers.id |
| `title` | VARCHAR(200) | YES | NULL | 커리큘럼 제목 |
| `status` | VARCHAR(20) | NO | 'draft' | 상태 |
| `purpose` | VARCHAR(30) | YES | NULL | 학습 목적 |
| `level` | VARCHAR(20) | YES | NULL | 사용자 수준 |
| `known_concepts` | TEXT[] | YES | NULL | 이미 아는 개념 |
| `budgeted_time` | JSONB | YES | NULL | 학습 시간 설정 |
| `preferred_resources` | TEXT[] | YES | NULL | 선호 리소스 타입 |
| `graph_data` | JSONB | YES | NULL | AI 생성 그래프 |
| `node_count` | INT | NO | 0 | 노드 수 (캐시) |
| `estimated_hours` | FLOAT | NO | 0 | 예상 학습시간 (캐시) |
| `created_at` | TIMESTAMP | NO | NOW() | 생성일시 |
| `updated_at` | TIMESTAMP | NO | NOW() | 수정일시 |

```sql
CREATE TABLE curriculums (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    title VARCHAR(200),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    purpose VARCHAR(30),
    level VARCHAR(20),
    known_concepts TEXT[],
    budgeted_time JSONB,
    preferred_resources TEXT[],
    graph_data JSONB,
    node_count INT NOT NULL DEFAULT 0,
    estimated_hours FLOAT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_curriculums_user_id ON curriculums(user_id);
CREATE INDEX idx_curriculums_status ON curriculums(status);
```

---

## Enum 값

### status (커리큘럼 상태)

| Value | Description |
|-------|-------------|
| `draft` | 초안 (논문 업로드 완료) |
| `options_saved` | 옵션 설정 완료 |
| `generating` | AI 생성 중 |
| `ready` | 생성 완료 |
| `failed` | 생성 실패 |

### purpose (학습 목적)

| Value | Description |
|-------|-------------|
| `deep_research` | 심층 연구 |
| `simple_study` | 개념 학습 |
| `trend_check` | 트렌드 파악 |
| `code_implementation` | 구현 실습 |
| `exam_preparation` | 시험 준비 |

### level (사용자 수준)

| Value | Description |
|-------|-------------|
| `non_major` | 입문자 |
| `bachelor` | 학부생 |
| `master` | 대학원생 |
| `researcher` | 연구원 |
| `industry` | 현업 |

### resource type (리소스 타입)

| Value | Description |
|-------|-------------|
| `paper` | 원문 논문 |
| `article` | 블로그/아티클 |
| `video` | 영상 강의 |
| `code` | 코드/튜토리얼 |

---

## graph_data JSONB 구조

```json
{
  "meta": {
    "paper_title": "Attention Is All You Need",
    "paper_authors": ["Vaswani", "Shazeer"],
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
          "description": "트랜스포머 시각화 설명",
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
```

---

## 관계 요약

| 관계 | 설명 |
|------|------|
| users 1:N refresh_tokens | 사용자당 여러 토큰 |
| users 1:N papers | 사용자당 여러 논문 |
| users 1:N curriculums | 사용자당 여러 커리큘럼 |
| papers 1:N curriculums | 논문당 여러 커리큘럼 |

---

## 총 테이블: 4개

1. `users`
2. `refresh_tokens`
3. `papers`
4. `curriculums`
