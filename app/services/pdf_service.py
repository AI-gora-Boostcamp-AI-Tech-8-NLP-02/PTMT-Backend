"""PDF Service - PDF 파일 처리

TODO: 실제 구현 시
- PyPDF2 또는 pdfplumber로 텍스트 추출
- AI로 논문 정보 추출 (제목, 저자, 초록, 키워드)
"""

from typing import Optional


async def extract_text(pdf_bytes: bytes) -> str:
    """PDF에서 텍스트 추출
    
    TODO: 실제 구현
    - PyPDF2: 기본 텍스트 추출
    - pdfplumber: 테이블 포함 추출
    - OCR: 스캔된 PDF 처리
    """
    # 더미 구현
    return "Extracted text from PDF... (dummy)"


async def extract_metadata(text: str) -> dict:
    """텍스트에서 논문 메타데이터 추출
    
    TODO: 실제 구현
    - AI (GPT, Claude)로 제목, 저자, 초록 추출
    - 정규식으로 DOI 추출
    """
    # 더미 구현
    return {
        "title": "Extracted Paper Title",
        "authors": ["Author 1", "Author 2"],
        "abstract": "Paper abstract...",
        "keywords": ["keyword1", "keyword2"],
    }


async def extract_keywords(text: str) -> list:
    """텍스트에서 핵심 키워드 추출
    
    TODO: 실제 구현
    - AI로 도메인 키워드 추출
    - 중요도 점수 계산
    - 연관 키워드 확장
    """
    # 더미 구현
    return [
        {"id": "kw-1", "name": "Keyword 1", "importance": 8},
        {"id": "kw-2", "name": "Keyword 2", "importance": 7},
    ]
