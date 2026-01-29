"""Paper service (stub).

Complex logic (upload to Supabase Storage, parsing PDFs, external search) will live here.
For now, API routes call these async stubs without implementing details.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx

from app import crud
from app.core.config import settings
from app.crud.errors import NotFoundError
from app.crud.supabase_client import get_supabase_client
from app.models.user import User
from app.services import pdf_service
from app.crud.users import ensure_user_exists


async def upload_pdf_to_storage(
    *, contents: bytes, user_id: str, filename: str
) -> tuple[str, str]:
    """PDF를 Supabase Storage에 업로드
    
    Args:
        contents: PDF 파일 내용
        user_id: 사용자 ID
        filename: 파일명
        
    Returns:
        (storage_path, pdf_url) 튜플
    """
    client = await get_supabase_client()
    
    # Storage 경로 생성: {user_id}/{uuid}.pdf
    file_id = uuid.uuid4()
    storage_path = f"{user_id}/{file_id}.pdf"
    
    # Supabase Storage에 업로드
    storage_response = await client.storage.from_("papers").upload(
        path=storage_path,
        file=contents,
        file_options={"content-type": "application/pdf"}
    )
    
    # 업로드된 파일의 공개 URL 생성
    pdf_url = await client.storage.from_("papers").get_public_url(storage_path)
    
    print(f"[PDF Upload] 파일 업로드 완료: {storage_path}")
    print(f"[PDF Upload] 공개 URL: {pdf_url}")
    
    return storage_path, pdf_url


async def create_curriculum_for_paper(
    *,
    user_id: str,
    paper_id: str,
    paper_title: str,
) -> dict[str, Any]:
    """Paper에 대한 빈 Curriculum을 생성하고 모든 관계를 연결
    
    Args:
        user_id: 사용자 ID
        paper_id: Paper ID
        paper_title: 논문 제목 (Curriculum 제목 생성에 사용)
        
    Returns:
        curriculum 딕셔너리
    """
    # 빈 Curriculum 생성 (paper만 첨부된 상태)
    curriculum = await crud.curriculums.create_curriculum(
        title=f"{paper_title} 학습 커리큘럼",
        status="paper_attached",  # Paper만 첨부된 상태
        purpose=None,
        level=None,
        known_concepts=None,
        budgeted_time=None,
        preferred_resources=None,
        graph_data=None,
        node_count=0,
        estimated_hours=0.0,
    )
    print(f"[Paper Service] Curriculum 생성 완료: {curriculum['id']}")
    
    # Curriculum-Paper 연결
    await crud.junctions.add_curriculum_paper(
        curriculum_id=str(curriculum["id"]),
        paper_id=paper_id,
    )
    print(f"[Paper Service] Curriculum-Paper 연결 완료")
    
    # User-Curriculum 연결
    await crud.junctions.add_user_curriculum(
        user_id=user_id,
        curriculum_id=str(curriculum["id"]),
    )
    print(f"[Paper Service] User-Curriculum 연결 완료")
    
    return curriculum


async def create_paper_with_curriculum(
    *,
    user_id: str,
    title: str,
    authors: list[str] | None = None,
    abstract: str | None = None,
    language: str = "english",
    source_url: str | None = None,
    pdf_storage_path: str | None = None,
    extracted_text: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Paper와 빈 Curriculum을 생성하고 모든 관계를 연결
    
    범용 함수: PDF, 링크, 검색 등 모든 방식에서 사용 가능
    
    Args:
        user_id: 사용자 ID
        title: 논문 제목
        authors: 저자 목록 (선택)
        abstract: 초록 (선택)
        language: 언어
        source_url: 원본 URL (선택)
        pdf_storage_path: Storage 경로 (선택)
        extracted_text: 추출된 본문 텍스트 (선택)
        
    Returns:
        (paper, curriculum) 튜플
    """
    # Paper 생성
    paper = await crud.papers.create_paper(
        title=title,
        authors=authors or ["Unknown Author"],
        abstract=abstract or "AI가 논문을 분석하여 핵심 개념을 추출했습니다.",
        language=language,
        source_url=source_url,
        pdf_storage_path=pdf_storage_path,
        extracted_text=extracted_text,
    )
    print(f"[Paper Service] Paper 생성 완료: {paper['id']}")
    
    # User-Paper 연결 (junction table)
    await crud.junctions.add_user_paper(
        user_id=user_id,
        paper_id=str(paper["id"]),
    )
    print(f"[Paper Service] User-Paper 연결 완료")
    
    # Curriculum 생성 및 연결
    curriculum = await create_curriculum_for_paper(
        user_id=user_id,
        paper_id=str(paper["id"]),
        paper_title=title,
    )
    
    return paper, curriculum


async def process_pdf_upload(
    *,
    contents: bytes,
    filename: str,
    user_id: str,
    user_email: str,
    user_name: str,
    user_avatar_url: str | None,
    user_role: str,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """PDF 업로드 전체 프로세스
    
    Args:
        contents: PDF 파일 내용
        filename: 파일명
        user_id: 사용자 ID
        user_email: 사용자 이메일
        user_name: 사용자 이름
        user_avatar_url: 프로필 이미지 URL
        user_role: 사용자 역할
        
    Returns:
        (paper, curriculum, pdf_url) 튜플
    """
    # 1. Supabase Storage에 업로드
    storage_path, pdf_url = await upload_pdf_to_storage(
        contents=contents,
        user_id=user_id,
        filename=filename,
    )
    
    # 2. PDF 텍스트 및 메타데이터 추출 (GROBID 사용)
    print(f"[PDF Processing] PDF 처리 시작: {filename}")
    print(f"[PDF Processing] 파일 크기: {len(contents)} bytes")
    
    try:
        # 2-1. GROBID로 메타데이터 추출
        print(f"[PDF Processing] 메타데이터 추출 중...")
        metadata = await pdf_service.extract_metadata(contents)
        print(f"[PDF Processing] 제목: {metadata['title']}")
        print(f"[PDF Processing] 저자: {len(metadata['authors'])}명")
        
        # 2-2. GROBID로 본문 텍스트 추출
        print(f"[PDF Processing] 본문 텍스트 추출 중...")
        extracted_text = await pdf_service.extract_text(contents)
        print(f"[PDF Processing] 추출된 텍스트 길이: {len(extracted_text)} characters")
        
    except Exception as e:
        print(f"[PDF Processing] GROBID 처리 실패: {e}")
        # 폴백: 기본 메타데이터 사용
        extracted_text = ""
        metadata = {
            "title": filename.replace(".pdf", ""),
            "authors": ["Unknown Author"],
            "abstract": "",
            "keywords": []
        }
    
    # 4. users 테이블에 사용자가 있는지 확인하
    await ensure_user_exists(
        user_id=user_id,
        email=user_email,
        name=user_name,
        avatar_url=user_avatar_url,
        role=user_role,
    )

    # 3. AI로 키워드 추출
    print(f"[AI Keyword Extraction] AI 키워드 추출 시작")
    keywords: list[str] = []
    summary: str | None = None
    
    # Paper를 먼저 생성하여 paper_id를 얻음
    paper_title = metadata.get("title") or filename.replace(".pdf", "")
    paper_authors = metadata.get("authors") or ["Unknown Author"]
    paper_abstract = metadata.get("abstract") or "초록을 추출할 수 없습니다."
    
    paper, curriculum = await create_paper_with_curriculum(
        user_id=user_id,
        title=paper_title,
        authors=paper_authors,
        abstract=paper_abstract,
        language="english",
        source_url=None,
        pdf_storage_path=storage_path,
        extracted_text=extracted_text,
    )

    paper_id = str(paper["id"])
    
    # 키워드 추출 API 호출
    try:
        api_url = (settings.KEYWORD_EXTRACTION_API_URL or "").rstrip("/")
        token = (settings.KEYWORD_EXTRACTION_API_TOKEN or "").strip()
        
        if api_url and token and extracted_text:
            keyword_api_url = f"{api_url}/api/curr/keywords/extract"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            
            # extracted_text가 JSON 형식일 경우 body 필드 추출
            paper_body = []
            if extracted_text:
                try:
                    # extracted_text가 JSON 문자열인 경우 파싱
                    if isinstance(extracted_text, str):
                        parsed_text = json.loads(extracted_text)
                        paper_body = parsed_text.get("body", [])
                    # 이미 딕셔너리인 경우
                    elif isinstance(extracted_text, dict):
                        paper_body = extracted_text.get("body", [])
                    # 그 외의 경우 원본 텍스트를 그대로 사용
                    else:
                        paper_body = [
                            {
                                "subtitle": "Full Text",
                                "text": str(extracted_text),
                            }
                        ]
                except (json.JSONDecodeError, AttributeError):
                    # JSON 파싱 실패 시 원본 텍스트를 그대로 사용
                    paper_body = [
                        {
                            "subtitle": "Full Text",
                            "text": extracted_text,
                        }
                    ]
            
            # paper_content 구조 생성
            paper_content = {
                "title": paper_title,
                "author": ", ".join(paper_authors) if paper_authors else "",
                "abstract": paper_abstract,
                "body": paper_body,
            }
            
            body = {
                "paper_id": paper_id,
                "paper_content": paper_content,
            }

            print(headers)
            print(body)
            
            print(f"[AI Keyword Extraction] API 호출: {keyword_api_url}")
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(keyword_api_url, json=body, headers=headers)
                resp.raise_for_status()
                result = resp.json()
                keywords = result.get("keywords", [])
                summary = result.get("summary")
                print(f"[AI Keyword Extraction] 추출된 키워드: {keywords}")
                print(f"[AI Keyword Extraction] 요약: {summary[:100] if summary else 'None'}...")
                
                # Paper 테이블에 keywords와 summary 업데이트
                await crud.papers.update_paper(
                    paper_id=paper_id,
                    keywords=keywords,
                    summary=summary,
                )
                print(f"[AI Keyword Extraction] Paper 업데이트 완료")
                paper["keywords"] = keywords
        else:
            print(f"[AI Keyword Extraction] API 설정이 없거나 추출된 텍스트가 없어 건너뜁니다.")
    except Exception as e:
        print(f"[AI Keyword Extraction] 키워드 추출 실패: {e}")
        # 실패해도 계속 진행
    
    # Paper와 Curriculum은 이미 생성되었으므로 반환만 함
    return paper, curriculum, pdf_url


async def submit_link_stub(*, url: str, user_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create dummy Paper + Curriculum rows for a link submission.

    This keeps business logic minimal while still persisting records to DB so
    Swagger Try-it-out can verify that data is actually inserted.
    """
    # users 테이블에 사용자가 있는지 확인
    try:
        await crud.users.get_user(user_id)
    except NotFoundError:
        # users 테이블에 사용자가 없으면 생성할 수 없음 (user_id만으로는 정보 부족)
        # 이 경우는 회원가입이 제대로 되지 않은 경우이므로 에러 발생
        raise ValueError(f"User {user_id} not found in users table. Please ensure the user is properly registered.")

    # 범용 함수 사용
    paper, curriculum = await create_paper_with_curriculum(
        user_id=user_id,
        title="URL에서 분석한 논문",
        authors=["Author from URL"],
        abstract="AI가 링크의 논문을 분석 중입니다. (더미 데이터)",
        language="english",
        source_url=url,
        pdf_storage_path=None,
    )

    return paper, curriculum


async def submit_search_stub(
    *,
    title: str,
    user_id: str,
    authors: list[str] | None = None,
    abstract: str | None = None,
    source_url: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """검색 결과를 통해 Paper + Curriculum 생성
    
    Args:
        title: 논문 제목
        user_id: 사용자 ID
        authors: 저자 목록 (선택)
        abstract: 초록 (선택)
        source_url: 원본 URL (선택)
        
    Returns:
        (paper, curriculum) 튜플
    """
    # users 테이블에 사용자가 있는지 확인
    try:
        await crud.users.get_user(user_id)
    except NotFoundError:
        raise ValueError(f"User {user_id} not found in users table. Please ensure the user is properly registered.")
    
    # 범용 함수 사용
    paper, curriculum = await create_paper_with_curriculum(
        user_id=user_id,
        title=title,
        authors=authors or ["Unknown Author"],
        abstract=abstract or "AI가 논문을 분석하여 핵심 개념을 추출했습니다.",
        language="english",
        source_url=source_url,
        pdf_storage_path=None,
    )
    
    return paper, curriculum


async def search_by_title_stub(*args: Any, **kwargs: Any) -> None:
    """검색 stub - 향후 실제 외부 API 검색 구현 예정"""
    return None

