"""Paper service: PDF 업로드/처리, 링크 제출, 논문 검색(arXiv)."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any
from urllib.parse import urlparse

import httpx

from app import crud
from app.core.config import settings
from app.crud.supabase_client import get_supabase_client
from app.services import pdf_service
from app.services.key_queue_service import key_queue_service
from app.crud.users import ensure_user_exists
from app.utils.arxiv_paper_search import search_arxiv_first_pdf


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
    
    await client.storage.from_("papers").upload(
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
    queue_task_id: str | None = None,
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
        queue_task_id: 클라이언트가 전달한 대기열 추적 ID (선택)
        
    Returns:
        (paper, curriculum, pdf_url) 튜플
    """
    # 1. PDF 텍스트 및 메타데이터 추출 (GROBID) — 제목 확보 후 캐시 조회용
    print(f"[PDF Processing] PDF 처리 시작: {filename}")
    print(f"[PDF Processing] 파일 크기: {len(contents)} bytes")
    try:
        print(f"[PDF Processing] 메타데이터 추출 중...")
        metadata = await pdf_service.extract_metadata(contents)
        print(f"[PDF Processing] 제목: {metadata['title']}")
        print(f"[PDF Processing] 저자: {len(metadata['authors'])}명")
        print(f"[PDF Processing] 본문 텍스트 추출 중...")
        extracted_text = await pdf_service.extract_text(contents)
        print(f"[PDF Processing] 추출된 텍스트 길이: {len(extracted_text)} characters")
    except Exception as e:
        print(f"[PDF Processing] GROBID 처리 실패: {e}")
        extracted_text = ""
        metadata = {
            "title": filename.replace(".pdf", ""),
            "authors": ["Unknown Author"],
            "abstract": "",
            "keywords": [],
        }

    # 2. 사용자 확인
    await ensure_user_exists(
        user_id=user_id,
        email=user_email,
        name=user_name,
        avatar_url=user_avatar_url,
        role=user_role,
    )

    paper_title = metadata.get("title") or filename.replace(".pdf", "")
    paper_authors = metadata.get("authors") or ["Unknown Author"]
    paper_abstract = metadata.get("abstract") or "초록을 추출할 수 없습니다."

    # 3. 제목으로 기존 paper 조회 (캐시) — 키워드 5개일 때만 캐시 히트
    existing = await crud.papers.get_paper_by_title(paper_title)
    keywords_list = existing.get("keywords") if existing else None
    keyword_count = len(keywords_list) if isinstance(keywords_list, list) else 0
    if existing is not None and keyword_count == 5:
        print(f"[PDF Processing] 캐시 히트: 업로드 생략, 기존 paper 재사용, 키워드 추출 생략 (키워드 {keyword_count}개)")
        # 캐시 히트: 업로드 생략, 기존 paper 재사용, 키워드 추출 생략
        await crud.junctions.ensure_user_paper(user_id=user_id, paper_id=str(existing["id"]))
        curriculum = await create_curriculum_for_paper(
            user_id=user_id,
            paper_id=str(existing["id"]),
            paper_title=paper_title,
        )
        storage_path = existing.get("pdf_storage_path")
        if storage_path:
            client = await get_supabase_client()
            pdf_url = await client.storage.from_("papers").get_public_url(storage_path)
        else:
            pdf_url = ""
        print(f"[PDF Processing] 기존 paper 조회 완료: {existing['id']}")
        return existing, curriculum, pdf_url

    # 4. 캐시 미스: Storage 업로드 후 새 paper 생성
    print(f"[PDF Processing] 캐시 미스: Storage 업로드 후 새 paper 생성")
    storage_path, pdf_url = await upload_pdf_to_storage(
        contents=contents,
        user_id=user_id,
        filename=filename,
    )
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

    # 5. 키워드 추출 API 호출 및 paper 업데이트
    print(f"[AI Keyword Extraction] AI 키워드 추출 시작")
    try:
        api_url = (settings.KEYWORD_EXTRACTION_API_URL or "").rstrip("/")
        token = (settings.KEYWORD_EXTRACTION_API_TOKEN or "").strip()
        if api_url and token and extracted_text:
            keyword_api_url = f"{api_url}/api/curr/keywords/extract"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            assigned_key_slot: int | None = None
            paper_body = []
            try:
                if isinstance(extracted_text, str):
                    parsed_text = json.loads(extracted_text)
                    paper_body = parsed_text.get("body", [])
                elif isinstance(extracted_text, dict):
                    paper_body = extracted_text.get("body", [])
                else:
                    paper_body = [{"subtitle": "Full Text", "text": str(extracted_text)}]
            except (json.JSONDecodeError, AttributeError):
                paper_body = [{"subtitle": "Full Text", "text": extracted_text}]
            paper_content = {
                "title": paper_title,
                "author": ", ".join(paper_authors) if paper_authors else "",
                "abstract": paper_abstract,
                "body": paper_body,
            }
            try:
                assigned_key_slot = await key_queue_service.acquire_slot(
                    task_type="keyword_extraction",
                    task_id=queue_task_id or paper_id,
                )
                body = {
                    "paper_id": paper_id,
                    "paper_content": paper_content,
                    "assigned_key_slot": assigned_key_slot,
                }
                print(
                    f"[AI Keyword Extraction] API 호출: {keyword_api_url} (slot={assigned_key_slot})"
                )
                async with httpx.AsyncClient(timeout=120.0) as client:
                    resp = await client.post(
                        keyword_api_url,
                        json=body,
                        headers=headers,
                    )
                    resp.raise_for_status()
                    result = resp.json()
                    keywords = result.get("keywords", [])
                    summary = result.get("summary")
                    print(f"[AI Keyword Extraction] 추출된 키워드: {keywords}")
                    await crud.papers.update_paper(
                        paper_id=paper_id,
                        keywords=keywords,
                        summary=summary,
                    )
                    paper["keywords"] = keywords
            finally:
                if assigned_key_slot is not None:
                    await key_queue_service.release_slot(assigned_key_slot)
        else:
            print(f"[AI Keyword Extraction] API 설정이 없거나 추출된 텍스트가 없어 건너뜁니다.")
    except Exception as e:
        print(f"[AI Keyword Extraction] 키워드 추출 실패: {e}")

    return paper, curriculum, pdf_url


# arXiv PDF URL: https://arxiv.org/pdf/1706.03762 or https://arxiv.org/pdf/1706.03762.pdf
_ARXIV_PDF_RE = re.compile(r"^https?://arxiv\.org/pdf/([a-zA-Z0-9.]+)(?:\.pdf)?$", re.IGNORECASE)


async def _download_pdf_from_url(url: str) -> tuple[bytes, str]:
    """Download PDF from URL and return (contents, filename).

    Accepts:
        - https://arxiv.org/pdf/<id>
        - Any URL whose path ends with .pdf
        - Any URL whose response Content-Type is application/pdf

    Raises:
        ValueError: If URL is not a PDF link or download fails/size exceeded.
    """
    parsed = urlparse(url)
    path = (parsed.path or "").rstrip("/")
    path_lower = path.lower()

    # Optional: allow only known PDF patterns before requesting (save a request for obvious non-PDF)
    # We still validate Content-Type after GET.

    timeout = 30.0
    max_bytes = settings.max_upload_size_bytes

    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ValueError(f"PDF 다운로드 실패: HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ValueError(f"PDF 다운로드 실패: {e!s}") from e

        content_type = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()
        is_pdf_content = content_type == "application/pdf"
        is_pdf_path = path_lower.endswith(".pdf")

        # arXiv PDF link
        arxiv_match = _ARXIV_PDF_RE.match(url)
        if arxiv_match:
            # arXiv often returns html for some endpoints; check content-type
            if not is_pdf_content:
                raise ValueError("해당 arXiv 링크에서 PDF를 받을 수 없습니다. URL이 PDF 직접 링크인지 확인해 주세요.")
            filename = f"{arxiv_match.group(1)}.pdf"
        elif is_pdf_content or is_pdf_path:
            if not is_pdf_content and is_pdf_path:
                # Path says .pdf but server might return something else
                if content_type and "application/pdf" not in content_type:
                    raise ValueError("PDF 링크가 아닙니다. (Content-Type이 application/pdf가 아님)")
            filename = path.split("/")[-1] if path_lower.endswith(".pdf") else "downloaded.pdf"
            if not filename or not filename.lower().endswith(".pdf"):
                filename = "downloaded.pdf"
        else:
            raise ValueError("PDF 링크가 아닙니다. (Content-Type이 application/pdf가 아니고, 경로도 .pdf로 끝나지 않음)")

        # Read body with size limit
        body = b""
        async for chunk in resp.aiter_bytes(chunk_size=65536):
            body += chunk
            if len(body) > max_bytes:
                raise ValueError(f"파일 크기가 {settings.MAX_UPLOAD_SIZE_MB}MB를 초과합니다.")

    return body, filename


async def submit_link(
    *,
    url: str,
    user_id: str,
    user_email: str,
    user_name: str,
    user_avatar_url: str | None,
    user_role: str,
    queue_task_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Download PDF from URL and process via process_pdf_upload.

    Returns:
        (paper, curriculum, pdf_url) same as process_pdf_upload.
    """
    contents, filename = await _download_pdf_from_url(url)
    return await process_pdf_upload(
        contents=contents,
        filename=filename,
        user_id=user_id,
        user_email=user_email,
        user_name=user_name,
        user_avatar_url=user_avatar_url,
        user_role=user_role,
        queue_task_id=queue_task_id,
    )


async def _process_pdf_and_attach_source(
    *,
    contents: bytes,
    filename: str,
    source_url: str | None,
    user_id: str,
    user_email: str,
    user_name: str,
    user_avatar_url: str | None,
    user_role: str,
    queue_task_id: str | None,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """PDF 처리 후 paper에 source_url 반영해 반환."""
    paper, curriculum, pdf_url = await process_pdf_upload(
        contents=contents,
        filename=filename,
        user_id=user_id,
        user_email=user_email,
        user_name=user_name,
        user_avatar_url=user_avatar_url,
        user_role=user_role,
        queue_task_id=queue_task_id,
    )
    if source_url and paper.get("id"):
        await crud.papers.update_paper(paper_id=str(paper["id"]), source_url=source_url)
        paper["source_url"] = source_url
    return paper, curriculum, pdf_url


async def search_by_title(
    *,
    query: str,
    user_id: str,
    user_email: str,
    user_name: str,
    user_avatar_url: str | None,
    user_role: str,
    queue_task_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    """자연어 검색 후 arXiv에서 query와 유사도가 가장 높은 논문의 PDF로 Paper/Curriculum 생성."""
    arxiv_result = await search_arxiv_first_pdf(query)
    if arxiv_result and arxiv_result.get("pdf_url"):
        try:
            contents, filename = await _download_pdf_from_url(arxiv_result["pdf_url"])
            return await _process_pdf_and_attach_source(
                contents=contents,
                filename=filename,
                source_url=arxiv_result.get("source_url"),
                user_id=user_id,
                user_email=user_email,
                user_name=user_name,
                user_avatar_url=user_avatar_url,
                user_role=user_role,
                queue_task_id=queue_task_id,
            )
        except ValueError:
            raise
        except Exception as e:
            print(f"[Search] arXiv PDF 다운로드/처리 실패: {e}")

    raise ValueError("검색 결과가 없습니다.")
