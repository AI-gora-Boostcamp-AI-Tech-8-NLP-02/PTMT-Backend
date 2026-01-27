"""Paper service (stub).

Complex logic (upload to Supabase Storage, parsing PDFs, external search) will live here.
For now, API routes call these async stubs without implementing details.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app import crud
from app.core.config import settings
from app.crud.errors import NotFoundError
from app.crud.supabase_client import get_supabase_client
from app.models.user import User


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


async def ensure_user_exists(user_id: str, email: str, name: str, avatar_url: str | None, role: str) -> None:
    """users 테이블에 사용자가 있는지 확인하고, 없으면 에러 발생
    
    Args:
        user_id: 사용자 ID
        email: 이메일
        name: 이름
        avatar_url: 프로필 이미지 URL
        role: 역할
        
    Raises:
        ValueError: users 테이블에 사용자가 없는 경우
    """
    try:
        await crud.users.get_user(user_id)
    except NotFoundError:
        # users 테이블에 사용자가 없으면 에러 발생
        raise ValueError(
            f"User {user_id} not found in users table. "
            "Please ensure the user is properly registered through signup."
        )


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
    
    # 2. PDF 텍스트 추출 (TODO: 실제 구현)
    print(f"[PDF Text Extraction] PDF 텍스트 추출 시작: {filename}")
    print(f"[PDF Text Extraction] 파일 크기: {len(contents)} bytes")
    # TODO: 실제 PDF 텍스트 추출 구현
    # extracted_text = await pdf_service.extract_text(contents)
    # print(f"[PDF Text Extraction] 추출된 텍스트 길이: {len(extracted_text)} characters")
    
    # 3. AI로 키워드 추출 (TODO: 실제 구현)
    print(f"[AI Keyword Extraction] AI 키워드 추출 시작")
    # TODO: 실제 AI 키워드 추출 구현
    # keywords = await ai_service.extract_keywords(extracted_text)
    # print(f"[AI Keyword Extraction] 추출된 키워드: {keywords}")
    
    # 4. users 테이블에 사용자가 있는지 확인하고, 없으면 생성
    await ensure_user_exists(
        user_id=user_id,
        email=user_email,
        name=user_name,
        avatar_url=user_avatar_url,
        role=user_role,
    )
    
    # 5. Paper와 Curriculum 생성 및 연결
    paper_title = filename.replace(".pdf", "") if filename else "Unknown Paper"
    paper, curriculum = await create_paper_with_curriculum(
        user_id=user_id,
        title=paper_title,
        authors=["Unknown Author"],  # TODO: PDF에서 추출
        abstract="AI가 논문을 분석하여 핵심 개념을 추출했습니다. (더미 데이터)",
        language="english",
        source_url=None,
        pdf_storage_path=storage_path,
    )
    
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

