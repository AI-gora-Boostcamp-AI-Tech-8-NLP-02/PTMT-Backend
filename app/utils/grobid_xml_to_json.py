"""GROBID XML to JSON Parser

GROBID에서 생성된 TEI XML 파일을 JSON 형식으로 변환합니다.
"""

import json
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

# TEI XML 네임스페이스 (GROBID가 사용하는 표준)
# 모든 XML 요소 앞에 이 네임스페이스가 붙습니다
NS = {'tei': 'http://www.tei-c.org/ns/1.0'}

# 네임스페이스를 포함한 태그를 쉽게 만들기 위한 헬퍼
def tei(tag: str) -> str:
    """TEI 네임스페이스가 포함된 태그를 반환합니다.
    
    Args:
        tag: 태그 이름 (예: 'title', 'author')
        
    Returns:
        네임스페이스가 포함된 태그 (예: '{http://www.tei-c.org/ns/1.0}title')
    
    Example:
        tei('title') -> '{http://www.tei-c.org/ns/1.0}title'
    """
    return f"{{{NS['tei']}}}{tag}"


def extract_text(element: ET.Element | None, skip_tags: set[str] | None = None) -> str:
    """XML 요소에서 텍스트를 추출합니다.
    
    Args:
        element: XML 요소
        skip_tags: 건너뛸 태그 이름 집합 (네임스페이스 포함)
        
    Returns:
        추출된 텍스트
    """
    if element is None:
        return ""
    
    if skip_tags is None:
        skip_tags = set()
    
    # 요소의 직접 텍스트
    text_parts = []
    if element.text:
        text_parts.append(element.text.strip())
    
    # 자식 요소들의 텍스트
    for child in element:
        # skip_tags에 포함된 태그는 건너뜀
        if child.tag not in skip_tags:
            child_text = extract_text(child, skip_tags)
            if child_text:
                text_parts.append(child_text)
        # 자식 요소 다음의 tail 텍스트
        if child.tail:
            text_parts.append(child.tail.strip())
    
    # 여러 공백을 하나로 합치고 앞뒤 공백 제거
    result = " ".join(text_parts).strip()
    # 연속된 공백을 하나로 합치기
    result = " ".join(result.split())
    return result


def parse_author(author_elem: ET.Element) -> str:
    """저자 정보를 파싱합니다.
    
    Args:
        author_elem: author XML 요소
        
    Returns:
        저자 정보 문자열 (형식: "이름 소속 이메일")
    """
    parts = []
    
    # 이름 정보
    pers_name = author_elem.find(f".//{tei('persName')}")
    if pers_name is not None:
        name_parts = []
        forenames = pers_name.findall(f".//{tei('forename')}")
        surname = pers_name.find(f".//{tei('surname')}")
        
        for forename in forenames:
            if forename.text:
                name_parts.append(forename.text.strip())
        
        if surname is not None and surname.text:
            name_parts.append(surname.text.strip())
        
        if name_parts:
            # 이름 뒤에 ∗ 추가 (equal contribution 표시)
            full_name = " ".join(name_parts)
            parts.append(f"{full_name}∗")
    
    # 소속 정보 - 첫 번째 유효한 소속만 사용
    # affiliation의 직접 자식 orgName 중 첫 번째만 사용
    affiliation = author_elem.find(f".//{tei('affiliation')}")
    if affiliation is not None:
        # type="department" 또는 type="institution"인 첫 번째 orgName 찾기
        org_name = None
        for org in affiliation.findall(tei('orgName')):
            org_type = org.get("type", "")
            if org_type in ["department", "institution"] and org.text and org.text.strip():
                org_name = org.text.strip()
                break
        
        if org_name:
            parts.append(org_name)
    
    # 이메일
    email = author_elem.find(f".//{tei('email')}")
    if email is not None and email.text:
        parts.append(email.text.strip())
    
    return " ".join(parts)


def parse_title(tei_header: ET.Element) -> str:
    """제목을 파싱합니다.
    
    Args:
        tei_header: teiHeader XML 요소
        
    Returns:
        제목 문자열
    """
    # titleStmt에서 제목 찾기
    title_stmt = tei_header.find(f".//{tei('titleStmt')}")
    if title_stmt is not None:
        title_elem = title_stmt.find(f".//{tei('title')}[@type='main']")
        if title_elem is not None:
            title_text = extract_text(title_elem).strip()
            if title_text:
                # GROBID lightweight 버전에서 가끔 불필요한 앞부분 텍스트가 포함되는 경우
                # 제목이 비정상적으로 길고(150자 이상) 마침표로 구분된 경우
                # 마지막 문장을 실제 제목으로 간주
                if len(title_text) > 150 and '.' in title_text:
                    last_period = title_text.rfind('.')
                    if last_period != -1 and last_period < len(title_text) - 1:
                        potential_title = title_text[last_period + 1:].strip()
                        # 마지막 부분이 실제 제목처럼 보이는 경우 (20자 이상, 대문자로 시작)
                        if len(potential_title) > 20 and potential_title[0].isupper():
                            return potential_title
                return title_text
    
    # analytic에서 제목 찾기
    analytic = tei_header.find(f".//{tei('analytic')}")
    if analytic is not None:
        title_elem = analytic.find(f".//{tei('title')}[@type='main']")
        if title_elem is not None:
            title_text = extract_text(title_elem).strip()
            if title_text:
                # 동일한 로직 적용
                if len(title_text) > 150 and '.' in title_text:
                    last_period = title_text.rfind('.')
                    if last_period != -1 and last_period < len(title_text) - 1:
                        potential_title = title_text[last_period + 1:].strip()
                        if len(potential_title) > 20 and potential_title[0].isupper():
                            return potential_title
                return title_text
    
    return ""


def parse_abstract(tei_header: ET.Element) -> str:
    """초록을 파싱합니다.
    
    Args:
        tei_header: teiHeader XML 요소
        
    Returns:
        초록 문자열
    """
    abstract_elem = tei_header.find(f".//{tei('abstract')}")
    if abstract_elem is None:
        return ""
    
    # 각주나 기여도 설명 등을 제외하기 위한 패턴
    # "* Equal contribution", "† Work performed", "‡ Work performed" 등으로 시작하는 단락 제외
    footnote_patterns = ["* ", "† ", "‡ ", "* Equal", "Work performed"]
    
    # abstract 안의 첫 번째 <p> 태그만 추출 (일반적으로 실제 초록)
    paragraphs = []
    for p in abstract_elem.findall(f".//{tei('p')}"):
        p_text = extract_text(p).strip()
        if p_text:
            # 각주로 보이는 단락은 제외
            is_footnote = any(p_text.startswith(pattern) for pattern in footnote_patterns)
            if not is_footnote:
                paragraphs.append(p_text)
            else:
                # 각주가 발견되면 이후 단락은 모두 각주로 간주하고 중단
                break
    
    return " ".join(paragraphs).strip()


def parse_authors(tei_header: ET.Element) -> list[str]:
    """저자 목록을 파싱합니다.
    
    Args:
        tei_header: teiHeader XML 요소
        
    Returns:
        저자 정보 문자열 리스트
    """
    authors = []
    
    # analytic 안의 모든 author 요소 찾기
    analytic = tei_header.find(f".//{tei('analytic')}")
    if analytic is not None:
        author_elems = analytic.findall(f".//{tei('author')}")
        for author_elem in author_elems:
            author_str = parse_author(author_elem)
            if author_str:
                authors.append(author_str)
    
    return authors


def parse_body(body_elem: ET.Element) -> list[dict[str, str]]:
    """본문을 파싱합니다.
    
    Args:
        body_elem: body XML 요소
        
    Returns:
        본문 섹션 리스트 (각 섹션은 subtitle과 text를 포함)
    """
    sections = []
    
    # body의 직접 자식 div 요소만 처리 (중첩된 div는 재귀적으로 처리)
    direct_divs = body_elem.findall(tei('div'))
    
    def process_div(div: ET.Element, parent_sections: list[dict[str, str]]) -> None:
        """div 요소를 재귀적으로 처리합니다."""
        # head 요소 (subtitle) - div의 직접 자식 head만
        head = div.find(tei('head'))
        
        subtitle = ""
        if head is not None:
            # head의 n 속성 (섹션 번호) 가져오기
            section_number = head.get("n", "")
            head_text = extract_text(head).strip()
            
            # 잘못된 섹션 제목 필터링
            # GROBID가 그림 캡션이나 기타 메타데이터를 섹션으로 잘못 인식하는 경우
            if head_text:
                # 패턴: "Input-Input", "Layer" + 숫자, "Figure" + 숫자 등
                invalid_patterns = [
                    "Input-Input",
                    "Output-Output", 
                    "Attention Visualizations"
                ]
                # 의심스러운 패턴 체크
                if any(pattern in head_text for pattern in invalid_patterns):
                    return  # 이 섹션은 무시
                # "Layer5", "Figure3" 같은 패턴 체크 (공백 없이 숫자가 붙은 경우)
                if re.search(r'(Layer|Figure|Table)\d+', head_text):
                    return  # 이 섹션은 무시
            
            # 섹션 번호와 제목 결합
            if section_number and head_text:
                subtitle = f"{section_number} {head_text}"
            elif head_text:
                subtitle = head_text
        
        # p 요소들 (text) - div의 직접 자식 p만 (중첩 div의 p는 제외)
        paragraphs = []
        for child in div:
            if child.tag == tei('p'):
                p_text = extract_text(child).strip()
                if p_text:
                    # "6 Results"와 같이 숫자로 시작하는 짧은 제목은 제외
                    # (이것은 실제로는 다음 섹션의 제목일 가능성이 높음)
                    if len(p_text) < 20 and p_text.split()[0].isdigit():
                        continue
                    paragraphs.append(p_text)
        
        text = " ".join(paragraphs).strip()
        
        # subtitle이나 text가 있는 경우 섹션 추가
        if subtitle or text:
            parent_sections.append({
                "subtitle": subtitle,
                "text": text
            })
        
        # 중첩된 div 처리
        nested_divs = div.findall(tei('div'))
        for nested_div in nested_divs:
            process_div(nested_div, parent_sections)
    
    # 모든 직접 자식 div 처리
    for div in direct_divs:
        process_div(div, sections)
    
    return sections


def parse_grobid_xml(xml_path: str | Path) -> dict[str, Any]:
    """GROBID XML 파일을 JSON 형식으로 파싱합니다.
    
    Args:
        xml_path: GROBID XML 파일 경로
        
    Returns:
        파싱된 논문 정보 딕셔너리
    """
    xml_path = Path(xml_path)
    
    if not xml_path.exists():
        raise FileNotFoundError(f"XML 파일을 찾을 수 없습니다: {xml_path}")
    
    # XML 파싱
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"XML 파싱 오류: {e}") from e
    
    # teiHeader 찾기
    tei_header = root.find(f".//{tei('teiHeader')}")
    if tei_header is None:
        raise ValueError("teiHeader를 찾을 수 없습니다.")
    
    # 제목 파싱
    title = parse_title(tei_header)
    
    # 저자 파싱
    authors = parse_authors(tei_header)
    
    # 초록 파싱
    abstract = parse_abstract(tei_header)
    
    # 본문 파싱
    body_elem = root.find(f".//{tei('body')}")
    body_sections = []
    if body_elem is not None:
        body_sections = parse_body(body_elem)
    
    # JSON 구조 생성
    result = {
        "title": title,
        "author": authors,
        "abstract": abstract,
        "body": body_sections
    }
    
    return result


def convert_grobid_xml_to_json(
    xml_path: str | Path,
    output_path: str | Path | None = None
) -> dict[str, Any]:
    """GROBID XML 파일을 JSON으로 변환합니다.
    
    Args:
        xml_path: GROBID XML 파일 경로
        output_path: 출력 JSON 파일 경로 (None이면 딕셔너리만 반환)
        
    Returns:
        파싱된 논문 정보 딕셔너리
    """
    result = parse_grobid_xml(xml_path)
    
    # JSON 파일로 저장
    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent="\t")
    
    return result
