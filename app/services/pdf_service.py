"""PDF Service - PDF 파일 처리

GROBID 공식 클라이언트를 사용하여 PDF에서 텍스트와 메타데이터를 추출합니다.
"""

import asyncio
import json
import tempfile
from pathlib import Path

from grobid_client.grobid_client import GrobidClient

from app.utils.grobid_xml_to_json import parse_grobid_xml


def _process_pdf_with_grobid(pdf_bytes: bytes) -> dict:
    """GROBID로 PDF 처리 (동기 함수)
    
    Args:
        pdf_bytes: PDF 파일 바이트
        
    Returns:
        파싱된 논문 정보 딕셔너리
    """
    # 1. 임시 파일 생성 (GrobidClient.process_pdf는 파일 경로를 요구)
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
        tmp_pdf.write(pdf_bytes)
        tmp_pdf_path = tmp_pdf.name
    
    # 2. 임시 출력 디렉토리
    with tempfile.TemporaryDirectory() as tmp_output_dir:
        try:
            # 3. GrobidClient 생성
            grobid_client = GrobidClient(check_server=False)
            
            # 4. process_pdf 호출 (동기 함수)
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
                flavor=None,
                start=-1,
                end=-1
            )
            
            # 5. 상태 확인
            if status != 200:
                raise ValueError(f"GROBID 처리 실패: status={status}, error={xml_text}")
            
            # 6. XML을 임시 파일로 저장 (parse_grobid_xml이 파일 경로를 요구)
            tmp_xml_path = Path(tmp_output_dir) / "temp.tei.xml"
            with open(tmp_xml_path, 'w', encoding='utf-8') as f:
                f.write(xml_text)
            
            # 7. XML 파싱하여 JSON으로 변환
            result = parse_grobid_xml(tmp_xml_path)
            
            return result
            
        finally:
            # 8. 임시 PDF 파일 삭제
            Path(tmp_pdf_path).unlink(missing_ok=True)


async def extract_text(pdf_bytes: bytes) -> str:
    """PDF에서 텍스트 추출
    
    GROBID 공식 클라이언트를 사용하여 PDF를 처리하고,
    추출된 정보를 JSON string으로 반환합니다.
    
    Args:
        pdf_bytes: PDF 파일 바이트 (Supabase Storage에서 다운로드한 것)
        
    Returns:
        JSON 형식의 문자열: {"title": "...", "author": [...], "abstract": "...", "body": [...]}
    """
    # 동기 함수를 비동기로 실행 (블로킹 방지)
    result = await asyncio.to_thread(_process_pdf_with_grobid, pdf_bytes)
    
    # JSON을 string으로 변환
    json_string = json.dumps(result, ensure_ascii=False, indent=2)
    
    return json_string


async def extract_metadata(pdf_bytes: bytes) -> dict:
    """PDF에서 논문 메타데이터 추출
    
    Args:
        pdf_bytes: PDF 파일 바이트
        
    Returns:
        메타데이터 딕셔너리: {"title": str, "authors": list[str], "abstract": str, "keywords": list}
    """
    # 동기 함수를 비동기로 실행
    result = await asyncio.to_thread(_process_pdf_with_grobid, pdf_bytes)
    
    return {
        "title": result.get("title", ""),
        "authors": result.get("author", []),
        "abstract": result.get("abstract", ""),
        "keywords": [],  # TODO: 키워드 추출 구현
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
