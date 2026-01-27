"""Papers Router - 논문 관련 API

TODO: 실제 구현 시
- PDF 파일 업로드 및 저장 (Supabase Storage)
- PDF 텍스트 추출 (PyPDF2, pdfplumber 등)
- AI 기반 키워드 추출
- 외부 논문 검색 API 연동 (arXiv, Semantic Scholar 등)
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query, status

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

    # Supabase Storage에 업로드
    pdf_url: str = ""
    
    try:
        client = await get_supabase_client()
        
        # Storage 경로 생성: {user_id}/{uuid}.pdf
        file_id = uuid.uuid4()
        storage_path = f"{current_user.id}/{file_id}.pdf"
        
        # Supabase Storage에 업로드
        # bucket 이름은 "papers"로 가정 (Supabase 대시보드에서 생성 필요)
        storage_response = await client.storage.from_("papers").upload(
            path=storage_path,
            file=contents,
            file_options={"content-type": "application/pdf"}
        )
        
        # 업로드된 파일의 공개 URL 생성
        pdf_url = await client.storage.from_("papers").get_public_url(storage_path)
        
        print(f"[PDF Upload] 파일 업로드 완료: {storage_path}")
        print(f"[PDF Upload] 공개 URL: {pdf_url}")
        
    except Exception as e:
        print(f"[PDF Upload Error] Supabase Storage 업로드 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}",
        )

    # PDF 텍스트 추출 (TODO: 실제 구현)
    print(f"[PDF Text Extraction] PDF 텍스트 추출 시작: {file.filename}")
    print(f"[PDF Text Extraction] 파일 크기: {len(contents)} bytes")
    # TODO: 실제 PDF 텍스트 추출 구현
    # extracted_text = await pdf_service.extract_text(contents)
    # print(f"[PDF Text Extraction] 추출된 텍스트 길이: {len(extracted_text)} characters")

    # AI로 키워드 추출 (TODO: 실제 구현)
    print(f"[AI Keyword Extraction] AI 키워드 추출 시작")
    # TODO: 실제 AI 키워드 추출 구현
    # keywords = await ai_service.extract_keywords(extracted_text)
    # print(f"[AI Keyword Extraction] 추출된 키워드: {keywords}")

    # Paper 테이블에 레코드 생성
    paper_title = file.filename.replace(".pdf", "") if file.filename else "Unknown Paper"
    
    try:
        # Paper 생성
        paper = await crud.papers.create_paper(
            title=paper_title,
            authors=["Unknown Author"],  # TODO: PDF에서 추출
            abstract="AI가 논문을 분석하여 핵심 개념을 추출했습니다. (더미 데이터)",  # TODO: PDF에서 추출
            language="english",
            source_url=None,
            pdf_storage_path=storage_path,  # Storage 경로 저장
        )
        
        # User-Paper 연결 (junction table)
        await crud.junctions.add_user_paper(
            user_id=current_user.id,
            paper_id=str(paper["id"]),
        )
        
        print(f"[PDF Upload] Paper 생성 완료: {paper['id']}")
        print(f"[PDF Upload] User-Paper 연결 완료")
        
        # 더미 curriculum_id (응답 스키마 호환을 위해)
        curriculum_id = f"curr-{uuid.uuid4().hex[:8]}"
        
        return ApiResponse.ok(
            PaperUploadResponse(
                paper_id=str(paper["id"]),
                curriculum_id=curriculum_id,
                title=paper_title,
                authors=paper.get("authors") or ["Unknown Author"],
                abstract=paper.get("abstract") or "AI가 논문을 분석하여 핵심 개념을 추출했습니다. (더미 데이터)",
                language=paper.get("language") or "english",
                keywords=DUMMY_KEYWORDS,
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

    TODO: 실제 구현
    1. URL 유효성 검사
    2. URL에서 PDF 다운로드 또는 메타데이터 추출
    3. arXiv, Semantic Scholar 등 API 활용
    4. Paper 및 Curriculum(draft) 생성
    """
    # TODO: URL 검증 및 논문 정보 추출
    # paper_info = await paper_service.fetch_from_url(str(data.url))
    try:
        paper_row, curriculum_row = await paper_service.submit_link_stub(url=str(data.url))
    except CrudConfigError:
        return ApiResponse.fail("DB_NOT_CONFIGURED", "DB 설정이 필요합니다.")

    return ApiResponse.ok(
        PaperUploadResponse(
            paper_id=str(paper_row["id"]),
            curriculum_id=str(curriculum_row["id"]),
            title=str(paper_row.get("title") or "URL에서 분석한 논문"),
            authors=paper_row.get("authors") or ["Author from URL"],
            abstract=str(paper_row.get("abstract") or "AI가 링크의 논문을 분석 중입니다. (더미 데이터)"),
            language=str(paper_row.get("language") or "english"),
            keywords=DUMMY_KEYWORDS,
            source_url=str(data.url),
        )
    )


@router.post("/search", response_model=ApiResponse[PaperUploadResponse])
async def search_by_title(
    data: TitleSearchRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[PaperUploadResponse]:
    """논문 제목 검색

    TODO: 실제 구현
    1. 외부 API로 논문 검색 (arXiv, Semantic Scholar, Google Scholar)
    2. 검색 결과에서 논문 정보 추출
    3. Paper 및 Curriculum(draft) 생성
    """
    # TODO: 외부 API로 검색
    # search_result = await paper_service.search_by_title(data.title)
    # if not search_result:
    #     return ApiResponse.fail("PAPER_SEARCH_NOT_FOUND", "논문을 찾을 수 없습니다.")
    await paper_service.search_by_title_stub(data=data, current_user=current_user)

    # 더미 응답
    paper_id = f"paper-{uuid.uuid4().hex[:8]}"
    curriculum_id = f"curr-{uuid.uuid4().hex[:8]}"

    return ApiResponse.ok(
        PaperUploadResponse(
            paper_id=paper_id,
            curriculum_id=curriculum_id,
            title=data.title,
            authors=["Vaswani et al."],
            abstract="AI가 논문을 분석하여 학습 경로를 생성합니다. (더미 데이터)",
            language="english",
            keywords=DUMMY_KEYWORDS,
        )
    )

