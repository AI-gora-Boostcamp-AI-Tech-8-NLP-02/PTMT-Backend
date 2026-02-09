"""Papers Router - 논문 관련 API

TODO: 실제 구현 시
- PDF 파일 업로드 및 저장 (Supabase Storage)
- PDF 텍스트 추출 (PyPDF2, pdfplumber 등)
- AI 기반 키워드 추출
- 외부 논문 검색 API 연동 (arXiv, Semantic Scholar 등)
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Query, status

from app.api.deps import get_current_user
from app import crud
from app.crud.errors import CrudConfigError, NotFoundError
from app.crud.supabase_client import get_supabase_client
from app.core.config import settings
from app.schemas.common import ApiResponse, PaginationInfo
from app.schemas.paper import (
    Keyword,
    LinkSubmitRequest,
    PaperUploadResponse,
    TitleSearchRequest,
)
from app.schemas.user import UserResponse
from app.services import paper_service

router = APIRouter(prefix="/papers", tags=["papers"])


# ===========================================
# 더미 키워드 데이터 (1차 추출: name만)
# ===========================================

DUMMY_KEYWORDS = [
    Keyword(name="Transformer"),
    Keyword(name="Attention"),
    Keyword(name="Self-Attention"),
    Keyword(name="Multi-Head Attention"),
    Keyword(name="Positional Encoding"),
    Keyword(name="Encoder-Decoder"),
    Keyword(name="Feed-Forward Network"),
    Keyword(name="Layer Normalization"),
]


@router.get("", response_model=ApiResponse[dict])
async def list_papers(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(10, ge=1, le=100, description="페이지당 항목 수"),
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[dict]:
    """논문 목록 조회 (단순 CRUD)"""

    try:
        items, total = await crud.papers.list_papers(page=page, limit=limit)
    except CrudConfigError:
        return ApiResponse.ok(
            {
                "items": [],
                "pagination": PaginationInfo(page=page, limit=limit, total=0, has_more=False),
            }
        )

    return ApiResponse.ok(
        {
            "items": items,
            "pagination": PaginationInfo(
                page=page,
                limit=limit,
                total=total,
                has_more=(page * limit) < total,
            ),
        }
    )


@router.get("/{paper_id}", response_model=ApiResponse[dict])
async def get_paper(
    paper_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[dict]:
    """논문 단일 조회 (단순 CRUD)"""

    try:
        row = await crud.papers.get_paper(paper_id)
    except CrudConfigError:
        return ApiResponse.fail("DB_NOT_CONFIGURED", "DB 설정이 필요합니다.")
    except NotFoundError:
        return ApiResponse.fail("PAPER_NOT_FOUND", "논문을 찾을 수 없습니다.")
    return ApiResponse.ok(row)


@router.delete("/{paper_id}", response_model=ApiResponse[dict])
async def delete_paper(
    paper_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[dict]:
    """논문 삭제 (단순 CRUD)"""

    try:
        await crud.papers.delete_paper(paper_id)
    except CrudConfigError:
        return ApiResponse.fail("DB_NOT_CONFIGURED", "DB 설정이 필요합니다.")
    except NotFoundError:
        return ApiResponse.fail("PAPER_NOT_FOUND", "논문을 찾을 수 없습니다.")
    return ApiResponse.ok({"message": "논문이 삭제되었습니다."})



@router.post("/pdf", response_model=ApiResponse[PaperUploadResponse])
async def upload_pdf(
    file: UploadFile = File(...),
    client_task_id: str | None = Form(None),
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[PaperUploadResponse]:
    """PDF 업로드

    1. 파일 검증 (크기, 형식)
    2. Supabase Storage에 업로드
    3. PDF 텍스트 추출 (TODO: 실제 구현)
    4. AI로 키워드 추출 (TODO: 실제 구현)
    """
    # 파일 형식 검증
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF 파일만 업로드 가능합니다.",
        )

    # 파일 내용 읽기
    contents = await file.read()
    
    # 파일 크기 검증
    if len(contents) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"파일 크기는 {settings.MAX_UPLOAD_SIZE_MB}MB를 초과할 수 없습니다.",
        )

    # PDF 업로드 및 처리
    try:
        paper, curriculum, pdf_url = await paper_service.process_pdf_upload(
            contents=contents,
            filename=file.filename,
            user_id=current_user.id,
            user_email=current_user.email,
            user_name=current_user.name,
            user_avatar_url=current_user.avatar_url,
            user_role=current_user.role,
            queue_task_id=client_task_id,
        )
        
        paper_title = file.filename.replace(".pdf", "") if file.filename else "Unknown Paper"
        
        # 키워드 데이터 처리: 문자열 리스트인 경우 Keyword 객체 리스트로 변환
        keywords_data = paper.get("keywords") or []
        keywords_response = []
        if keywords_data:
            if isinstance(keywords_data[0], str):
                keywords_response = [Keyword(name=k) for k in keywords_data]
            else:
                keywords_response = keywords_data

        return ApiResponse.ok(
            PaperUploadResponse(
                paper_id=str(paper["id"]),
                curriculum_id=str(curriculum["id"]),
                title=paper_title,
                authors=paper.get("authors") or ["Unknown Author"],
                abstract=paper.get("abstract") or "AI가 논문을 분석하여 핵심 개념을 추출했습니다. (더미 데이터)",
                language=paper.get("language") or "english",
                keywords=keywords_response,
                pdf_url=pdf_url,
            )
        )
        
    except Exception as e:
        print(f"[PDF Upload Error] DB 저장 실패: {e}")
        # Storage에 업로드는 성공했지만 DB 저장 실패 시에도 응답 반환
        # (나중에 수동으로 정리 가능)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"논문 정보 저장 중 오류가 발생했습니다: {str(e)}",
        )


@router.post("/link", response_model=ApiResponse[PaperUploadResponse])
async def submit_link(
    data: LinkSubmitRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[PaperUploadResponse]:
    """링크 제출

    PDF 직접 링크(예: https://arxiv.org/pdf/1706.03762)를 다운로드 후
    process_pdf_upload와 동일하게 처리하여 Paper 및 Curriculum 생성.
    """
    try:
        paper_row, curriculum_row, pdf_url = await paper_service.submit_link(
            url=str(data.url),
            user_id=current_user.id,
            user_email=current_user.email,
            user_name=current_user.name,
            user_avatar_url=current_user.avatar_url,
            user_role=current_user.role,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CrudConfigError:
        return ApiResponse.fail("DB_NOT_CONFIGURED", "DB 설정이 필요합니다.")

    keywords_data = paper_row.get("keywords") or []
    keywords_response = (
        [Keyword(name=k) for k in keywords_data]
        if keywords_data and isinstance(keywords_data[0], str)
        else (keywords_data if keywords_data else [])
    )

    return ApiResponse.ok(
        PaperUploadResponse(
            paper_id=str(paper_row["id"]),
            curriculum_id=str(curriculum_row["id"]),
            title=str(paper_row.get("title") or "URL에서 분석한 논문"),
            authors=paper_row.get("authors") or ["Unknown Author"],
            abstract=str(paper_row.get("abstract") or "AI가 링크의 논문을 분석 중입니다."),
            language=str(paper_row.get("language") or "english"),
            keywords=keywords_response,
            source_url=str(data.url),
            pdf_url=pdf_url,
        )
    )


@router.post("/search", response_model=ApiResponse[PaperUploadResponse])
async def search_by_title(
    data: TitleSearchRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[PaperUploadResponse]:
    """논문 제목/자연어 검색

    Semantic Scholar로 검색한 뒤 첫 번째 논문의 PDF로만 Paper 및 Curriculum 생성.
    PDF를 사용할 수 없으면(openAccessPdf 없음 또는 다운로드/처리 실패) 400 응답.
    """
    try:
        paper_row, curriculum_row, pdf_url = await paper_service.search_by_title(
            query=data.title,
            user_id=current_user.id,
            user_email=current_user.email,
            user_name=current_user.name,
            user_avatar_url=current_user.avatar_url,
            user_role=current_user.role,
        )
    except ValueError as e:
        msg = str(e)
        if "검색 결과가 없습니다" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        # PDF 사용 불가(openAccessPdf 없음 또는 다운로드/처리 실패)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except CrudConfigError:
        return ApiResponse.fail("DB_NOT_CONFIGURED", "DB 설정이 필요합니다.")
    except Exception as e:
        print(f"[Search Error] 검색 중 오류 발생: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"논문 검색 중 오류가 발생했습니다: {str(e)}",
        )

    keywords_data = paper_row.get("keywords") or []
    keywords_response = (
        [Keyword(name=k) for k in keywords_data]
        if keywords_data and isinstance(keywords_data[0], str)
        else (keywords_data if keywords_data else [])
    )

    return ApiResponse.ok(
        PaperUploadResponse(
            paper_id=str(paper_row["id"]),
            curriculum_id=str(curriculum_row["id"]),
            title=str(paper_row.get("title") or data.title),
            authors=paper_row.get("authors") or ["Unknown Author"],
            abstract=str(paper_row.get("abstract") or "AI가 논문을 분석하여 핵심 개념을 추출했습니다."),
            language=str(paper_row.get("language") or "english"),
            keywords=keywords_response,
            source_url=paper_row.get("source_url"),
            pdf_url=pdf_url,
        )
    )
