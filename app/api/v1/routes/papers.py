"""Papers Router - 논문 관련 API

TODO: 실제 구현 시
- PDF 파일 업로드 및 저장 (Supabase Storage)
- PDF 텍스트 추출 (PyPDF2, pdfplumber 등)
- AI 기반 키워드 추출
- 외부 논문 검색 API 연동 (arXiv, Semantic Scholar 등)
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.schemas.common import ApiResponse
from app.schemas.paper import (
    Keyword,
    LinkSubmitRequest,
    PaperUploadResponse,
    TitleSearchRequest,
)
from app.schemas.user import UserResponse

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


@router.post("/pdf", response_model=ApiResponse[PaperUploadResponse])
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[PaperUploadResponse]:
    """PDF 업로드
    
    TODO: 실제 구현
    1. 파일 검증 (크기, 형식)
    2. Supabase Storage에 업로드
    3. PDF 텍스트 추출
    4. AI로 제목, 저자, 초록, 키워드 추출
    5. Paper 및 Curriculum(draft) 생성
    """
    # 파일 검증
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF 파일만 업로드 가능합니다.",
        )
    
    # 파일 크기 체크
    # TODO: 실제 구현 시 파일 크기 검증
    # contents = await file.read()
    # if len(contents) > settings.max_upload_size_bytes:
    #     raise HTTPException(
    #         status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    #         detail=f"파일 크기는 {settings.MAX_UPLOAD_SIZE_MB}MB를 초과할 수 없습니다.",
    #     )
    
    # TODO: Supabase Storage에 업로드
    # storage_path = f"papers/{current_user.id}/{uuid.uuid4()}.pdf"
    # await supabase.storage.upload(storage_path, contents)
    
    # TODO: PDF 텍스트 추출
    # extracted_text = await pdf_service.extract_text(contents)
    
    # TODO: AI로 키워드 추출
    # keywords = await ai_service.extract_keywords(extracted_text)
    
    # 더미 응답
    paper_id = f"paper-{uuid.uuid4().hex[:8]}"
    curriculum_id = f"curr-{uuid.uuid4().hex[:8]}"
    paper_title = file.filename.replace(".pdf", "") if file.filename else "Unknown Paper"
    
    return ApiResponse.ok(
        PaperUploadResponse(
            paper_id=paper_id,
            curriculum_id=curriculum_id,
            title=paper_title,
            authors=["Unknown Author"],
            abstract="AI가 논문을 분석하여 핵심 개념을 추출했습니다. (더미 데이터)",
            language="english",
            keywords=DUMMY_KEYWORDS,
            pdf_url=f"https://storage.example.com/papers/{paper_id}.pdf",
        )
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
    
    # 더미 응답
    paper_id = f"paper-{uuid.uuid4().hex[:8]}"
    curriculum_id = f"curr-{uuid.uuid4().hex[:8]}"
    
    return ApiResponse.ok(
        PaperUploadResponse(
            paper_id=paper_id,
            curriculum_id=curriculum_id,
            title="URL에서 분석한 논문",
            authors=["Author from URL"],
            abstract="AI가 링크의 논문을 분석 중입니다. (더미 데이터)",
            language="english",
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
