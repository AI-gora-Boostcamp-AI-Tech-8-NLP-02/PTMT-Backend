# GROBID 설치 및 파싱 완전 가이드

이 문서는 GROBID 설치부터 논문 PDF 파싱까지의 전체 과정을 단계별로 설명합니다.

---

## 목차

1. [개요](#개요)
2. [GROBID 설치](#grobid-설치)
3. [GROBID 서버 실행](#grobid-서버-실행)
4. [시스템 아키텍처](#시스템-아키텍처)
5. [파싱 프로세스 상세](#파싱-프로세스-상세)
6. [코드 구조](#코드-구조)
7. [테스트 방법](#테스트-방법)
8. [문제 해결](#문제-해결)
9. [참고 자료](#참고-자료)

---

## 개요

### GROBID란?

**GROBID (GeneRation Of Bibliographic Data)**는 학술 논문 PDF에서 구조화된 정보를 추출하는 오픈소스 도구입니다.

**주요 기능**:
- 논문 제목, 저자, 초록 추출
- 본문 섹션 구조 파싱
- 참고문헌 인식
- 메타데이터 추출

**출력 형식**: TEI XML (Text Encoding Initiative 표준)

### 시스템 구성

```
PDF 파일 (Supabase Storage)
    ↓
paper_service.py (업로드 처리)
    ↓
pdf_service.py (GROBID API 호출)
    ↓
grobid_xml_to_json.py (XML → JSON 변환)
    ↓
JSON 데이터 (Paper 테이블 저장)
```

---

## GROBID 설치

### 1. 필수 요구사항

- **OS**: Linux (Ubuntu/Debian 권장)
- **Java**: OpenJDK 17 이상
- **메모리**: 최소 4GB RAM (권장 8GB+)
- **디스크**: 최소 2GB 여유 공간

### 2. 자동 설치 스크립트

프로젝트에 포함된 설치 스크립트를 사용합니다:

```bash
# 스크립트 실행 권한 부여
chmod +x scripts/grobid_setting.sh

# 설치 실행
./scripts/grobid_setting.sh
```

**스크립트가 수행하는 작업**:

1. **필수 패키지 설치**
   ```bash
   apt-get update
   apt-get install -y curl sudo wget unzip tmux openjdk-17-jdk
   ```

2. **GROBID 다운로드**
   ```bash
   wget https://github.com/kermitt2/grobid/archive/0.8.2.zip
   unzip 0.8.2.zip
   ```

3. **GROBID 빌드**
   ```bash
   cd grobid-0.8.2
   ./gradlew clean install
   ```

4. **서버 실행** (tmux 세션에서)
   ```bash
   tmux new-session -d -s grobid "./gradlew run"
   ```

### 3. 수동 설치

자동 스크립트를 사용할 수 없는 경우:

```bash
# 1. Java 설치
sudo apt update
sudo apt install -y openjdk-17-jdk

# 2. GROBID 다운로드
wget https://github.com/kermitt2/grobid/archive/0.8.2.zip
unzip 0.8.2.zip
cd grobid-0.8.2

# 3. 빌드
./gradlew clean install

# 4. 서버 실행
./gradlew run
```

### 4. 설치 확인

```bash
# GROBID 서버 상태 확인
curl http://localhost:8070/api/isalive

# 응답: "true" (서버 실행 중)
```

---

## GROBID 서버 실행

### 1. 서버 시작

tmux 세션 사용 (권장)

```bash
cd grobid-0.8.2
tmux new-session -d -s grobid "./gradlew run"

# 세션 확인
tmux attach -t grobid

```

### 2. 서버 상태 확인

```bash
# 헬스 체크
curl http://localhost:8070/api/isalive

# 서버 정보
curl http://localhost:8070/api/version
```

### 3. 서버 중지

```bash
# tmux 세션 종료
tmux kill-session -t grobid

# 또는 프로세스 종료
pkill -f "grobid"
```

### 4. 서버 설정

기본 포트: `8070`

포트 변경이 필요한 경우:
```bash
# grobid-0.8.2/grobid-home/config/grobid.yaml 수정
# server.port: 8070 → 원하는 포트로 변경
```

---

## 시스템 아키텍처

### 전체 데이터 흐름

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PDF 업로드 (Supabase Storage)                            │
│    - paper_service.py: process_pdf_upload()                 │
│    - PDF bytes 다운로드                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. PDF 처리 (GROBID)                                         │
│    - pdf_service.py: extract_metadata() / extract_text()    │
│    - GrobidClient.process_pdf() 호출                        │
│    - PDF → TEI XML 변환                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. XML 파싱 (JSON 변환)                                      │
│    - grobid_xml_to_json.py: parse_grobid_xml()              │
│    - TEI XML → JSON dict 변환                               │
│    - 제목, 저자, 초록, 본문 추출                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. 데이터 저장 (Supabase)                                    │
│    - crud/papers.py: create_paper()                         │
│    - papers 테이블에 저장                                    │
│    - extracted_text: JSON string으로 저장                    │
└─────────────────────────────────────────────────────────────┘
```

### 주요 컴포넌트

#### 1. `app/services/paper_service.py`
- **역할**: PDF 업로드 전체 프로세스 관리
- **주요 함수**:
  - `process_pdf_upload()`: PDF 업로드 및 처리 오케스트레이션
  - `upload_pdf_to_storage()`: Supabase Storage에 PDF 업로드
  - `create_paper_with_curriculum()`: Paper 및 Curriculum 생성

#### 2. `app/services/pdf_service.py`
- **역할**: GROBID와의 통신 및 PDF 처리
- **주요 함수**:
  - `extract_text()`: PDF에서 전체 텍스트 추출 (JSON string 반환)
  - `extract_metadata()`: PDF에서 메타데이터 추출 (dict 반환)
  - `_process_pdf_with_grobid()`: GROBID API 호출 (내부 함수)

#### 3. `app/utils/grobid_xml_to_json.py`
- **역할**: GROBID XML을 JSON으로 변환
- **주요 함수**:
  - `parse_grobid_xml()`: XML 파일 파싱
  - `parse_title()`: 제목 추출
  - `parse_author()`: 저자 정보 추출
  - `parse_abstract()`: 초록 추출
  - `parse_body()`: 본문 섹션 추출

---

## 파싱 프로세스 상세

### 1. PDF → XML 변환

**GROBID API 호출** (`pdf_service.py`):

```python
grobid_client = GrobidClient(check_server=False)
pdf_file, status, xml_text = grobid_client.process_pdf(
    service="processFulltextDocument",
    pdf_file=tmp_pdf_path,
    generateIDs=False,
    consolidate_header=True,
    consolidate_citations=False,
    include_raw_citations=False,
    include_raw_affiliations=False,
    tei_coordinates=False,
    segment_sentences=False,
)
```

**입력**: PDF 파일 경로  
**출력**: TEI XML 문자열

### 2. XML → JSON 변환

**파싱 단계** (`grobid_xml_to_json.py`):

#### 2.1 제목 파싱 (`parse_title`)

**XML 구조**:
```xml
<title level="a" type="main">
    Provided proper attribution is provided... Attention Is All You Need
</title>
```

**처리 로직**:
- 비정상적으로 긴 제목(>150자)이고 마침표가 있는 경우
- 마지막 마침표 이후의 텍스트를 실제 제목으로 추출
- 예: `"Attention Is All You Need"`

**출력**:
```json
{
  "title": "Attention Is All You Need"
}
```

#### 2.2 저자 파싱 (`parse_author`)

**XML 구조**:
```xml
<author>
    <persName>
        <forename type="first">Ashish</forename>
        <surname>Vaswani</surname>
    </persName>
    <email>avaswani@google.com</email>
    <affiliation key="aff0">
        <orgName type="institution">Google Brain</orgName>
    </affiliation>
</author>
```

**처리 로직**:
1. 이름 추출: `forename` + `surname`
2. 소속 추출: 첫 번째 `type="institution"` 또는 `type="department"`만 사용
3. 이메일 추출: `<email>` 태그
4. 형식: `"이름∗ 소속 이메일"` (∗는 equal contribution 표시)

**출력**:
```json
{
  "author": [
    "Ashish Vaswani∗ Google Brain avaswani@google.com",
    "Noam Shazeer∗ Google Brain"
  ]
}
```

#### 2.3 초록 파싱 (`parse_abstract`)

**XML 구조**:
```xml
<abstract>
    <div xmlns="http://www.tei-c.org/ns/1.0">
        <p>The dominant sequence transduction models...</p>
        <p>* Equal contribution. Listing order is random...</p>
        <p>† Work performed while at Google Brain.</p>
    </div>
</abstract>
```

**처리 로직**:
- 각주 패턴 감지 및 제외:
  - `"* "`, `"† "`, `"‡ "`로 시작하는 단락
  - `"* Equal"`, `"Work performed"` 포함 단락
- 각주가 아닌 단락만 추출

**출력**:
```json
{
  "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks..."
}
```

#### 2.4 본문 파싱 (`parse_body`)

**XML 구조**:
```xml
<body>
    <div xmlns="http://www.tei-c.org/ns/1.0">
        <head n="1">Introduction</head>
        <p>Recurrent neural networks...</p>
        
        <div>
            <head n="1.1">Subsection</head>
            <p>Subsection content...</p>
        </div>
    </div>
</body>
```

**처리 로직**:
1. 재귀적으로 중첩된 `<div>` 처리
2. 섹션 번호 추출: `<head n="1">` → `"1 Introduction"`
3. 잘못된 섹션 필터링:
   - `"Input-Input Layer5"` 같은 패턴 제외
   - `"Figure3"`, `"Table2"` 같은 패턴 제외
4. 텍스트 추출: `<p>` 태그 내용만 추출

**출력**:
```json
{
  "body": [
    {
      "subtitle": "1 Introduction",
      "text": "Recurrent neural networks, long short-term memory..."
    },
    {
      "subtitle": "1.1 Subsection",
      "text": "Subsection content..."
    }
  ]
}
```

### 3. 최종 JSON 구조

```json
{
  "title": "Attention Is All You Need",
  "author": [
    "Ashish Vaswani∗ Google Brain avaswani@google.com",
    "Noam Shazeer∗ Google Brain"
  ],
  "abstract": "The dominant sequence transduction models...",
  "body": [
    {
      "subtitle": "1 Introduction",
      "text": "Recurrent neural networks..."
    },
    {
      "subtitle": "2 Background",
      "text": "The goal of reducing sequential computation..."
    }
  ]
}
```

### 4. 데이터베이스 저장

**저장 형식**:
- `title`, `authors`, `abstract`: 별도 컬럼에 저장
- `extracted_text`: 전체 JSON을 **string으로 변환**하여 저장

```python
# paper_service.py
extracted_text = await pdf_service.extract_text(contents)  # JSON string

# crud/papers.py
paper = await create_paper(
    title=metadata['title'],
    authors=metadata['authors'],
    abstract=metadata['abstract'],
    extracted_text=extracted_text,  # JSON string
)
```

---

## 코드 구조

### 파일 구조

```
app/
├── services/
│   ├── paper_service.py      # PDF 업로드 오케스트레이션
│   └── pdf_service.py         # GROBID 통신
├── utils/
│   └── grobid_xml_to_json.py # XML → JSON 변환
└── crud/
    └── papers.py              # 데이터베이스 저장

scripts/
├── grobid_setting.sh          # GROBID 설치 스크립트
└── test_pdf_service.py        # 통합 테스트
```

### 주요 함수 호출 체인

```python
# 1. API 엔드포인트
POST /api/papers/upload
    ↓
# 2. paper_service.py
process_pdf_upload()
    ├─ upload_pdf_to_storage()      # Supabase Storage 업로드
    ├─ pdf_service.extract_metadata()  # 메타데이터 추출
    ├─ pdf_service.extract_text()      # 텍스트 추출
    └─ create_paper_with_curriculum()  # DB 저장
        ↓
# 3. pdf_service.py
extract_text() / extract_metadata()
    └─ _process_pdf_with_grobid()
        ├─ GrobidClient.process_pdf()  # GROBID API 호출
        └─ parse_grobid_xml()          # XML 파싱
            ↓
# 4. grobid_xml_to_json.py
parse_grobid_xml()
    ├─ parse_title()
    ├─ parse_authors()
    ├─ parse_abstract()
    └─ parse_body()
        ↓
# 5. crud/papers.py
create_paper()
    └─ Supabase insert
```

---

## 테스트 방법

### 1. GROBID 서버 테스트

```bash
# 서버 상태 확인
curl http://localhost:8070/api/isalive

# 간단한 PDF 처리 테스트
curl -X POST -F "input=@test.pdf" \
  http://localhost:8070/api/processFulltextDocument \
  > output/test.grobid.tei.xml
```

### 2. 통합 테스트 (Supabase Storage PDF)

```bash
# PDF Service 전체 테스트
python scripts/test_pdf_service.py
```

**테스트 내용**:
- Supabase Storage URL에서 PDF 다운로드
- `extract_metadata()` 호출
- `extract_text()` 호출
- JSON 파싱 확인
- 결과 파일 저장

### 3. 단일 논문 파싱 테스트

```bash
# XML 파일 직접 파싱
python scripts/test_improved_grobid_parser.py
```

### 4. 여러 논문 일괄 테스트

```bash
# output/ 폴더의 모든 .tei.xml 파일 테스트
python scripts/test_multiple_papers.py
```

**출력 예시**:
```
총 3개 논문 테스트:
  ✓ 성공: 3개
  ✗ 실패: 0개

성공한 논문들:
  - Attention is all you need
    제목 길이: 26자
    저자: 8명
    섹션: 22개
```

## 참고 자료

### 공식 문서

- **GROBID**: https://grobid.readthedocs.io/
- **TEI XML**: https://tei-c.org/
- **grobid-client-python**: https://github.com/kermitt2/grobid-client-python

### 프로젝트 내 문서

- `README_GROBID_PARSER.md`: 파서 사용법
- `GENERALIZATION_GUIDE.md`: 일반화 가이드
- `docs/RDB_SCHEMA.md`: 데이터베이스 스키마

### 관련 스크립트

- `scripts/grobid_setting.sh`: GROBID 설치 스크립트
- `scripts/test_pdf_service.py`: 통합 테스트
- `scripts/test_multiple_papers.py`: 일괄 테스트

---

## 요약

이 가이드는 GROBID 설치부터 논문 파싱까지의 전체 과정을 다룹니다:

1. **설치**: `grobid_setting.sh` 스크립트로 자동 설치
2. **서버 실행**: tmux 세션에서 백그라운드 실행
3. **PDF 처리**: `pdf_service.py`가 GROBID API 호출
4. **XML 파싱**: `grobid_xml_to_json.py`가 JSON으로 변환
5. **데이터 저장**: `crud/papers.py`가 Supabase에 저장

전체 프로세스는 **비동기**로 처리되어 성능을 최적화하고, **에러 처리**를 통해 안정성을 보장합니다.
