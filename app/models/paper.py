"""Paper Model - 논문 테이블 정의

TODO: Supabase PostgreSQL 테이블과 연동
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Column
from sqlalchemy import ARRAY, String


class Paper(SQLModel, table=True):
    """논문 모델
    
    TODO: 실제 DB 연결 시 구현
    - PDF 파일 Supabase Storage 연동
    - 텍스트 추출 및 저장
    - DOI 기반 중복 체크
    """
    __tablename__ = "papers"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(max_length=500)
    authors: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))
    abstract: Optional[str] = Field(default=None)
    language: str = Field(default="english", max_length=20)
    source_url: Optional[str] = Field(default=None)
    doi: Optional[str] = Field(default=None, max_length=100)
    pdf_storage_path: Optional[str] = Field(default=None)
    extracted_text: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
