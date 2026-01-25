"""Paper Schemas - 논문 관련 요청/응답 스키마"""

from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class Keyword(BaseModel):
    """추출된 키워드 (1차 추출: name만)"""
    name: str


class LinkSubmitRequest(BaseModel):
    """링크 제출 요청"""
    url: HttpUrl


class TitleSearchRequest(BaseModel):
    """논문 제목 검색 요청"""
    title: str


class PaperUploadResponse(BaseModel):
    """논문 업로드/분석 응답
    
    PDF 업로드, 링크 제출, 제목 검색 모두 동일한 응답 형식
    """
    paper_id: str
    curriculum_id: str
    title: str
    authors: Optional[List[str]] = None
    abstract: str
    language: str = "english"
    keywords: List[Keyword]
    source_url: Optional[str] = None
    pdf_url: Optional[str] = None
