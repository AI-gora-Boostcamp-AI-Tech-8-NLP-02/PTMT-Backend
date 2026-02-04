"""Curriculum generation service.

외부 커리큘럼 생성 API를 호출하여 학습 경로를 생성합니다.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import settings
from app.crud import curriculums, papers

CURR_GENERATE_PATH = "/api/curr/curr/generate"


def _build_user_traits(curriculum: dict[str, Any]) -> dict[str, Any]:
    """Curriculum 객체에서 사용자 특성(user_traits) 딕셔너리를 생성합니다.
    
    Args:
        curriculum: Curriculum 딕셔너리 (DB에서 조회한 결과)
        
    Returns:
        user_traits 딕셔너리:
        {
            "purpose": str | None,
            "level": str | None,
            "known_concepts": list[str] | None,
            "budgeted_time": dict | None,
            "preferred_resources": list[str] | None
        }
    """
    return {
        "purpose": curriculum.get("purpose"),
        "level": curriculum.get("level"),
        "known_concepts": curriculum.get("known_concepts") or [],
        "budgeted_time": curriculum.get("budgeted_time"),
        "preferred_resources": curriculum.get("preferred_resources") or [],
    }


async def start_generation(curriculum_id: str) -> dict[str, Any] | None:
    """외부 커리큘럼 생성 API를 호출하여 생성 작업을 시작합니다.

    - curriculum_id로 커리큘럼 및 연결된 논문 정보를 조회한 뒤
    - 명세에 맞는 body로 POST /api/curr/curr/generate 호출
    - Bearer 토큰은 .env의 CURRICULUM_GENERATION_API_TOKEN 사용

    Returns:
        성공 시 응답 JSON (curriculum_id, success, status 등), 실패 시 None 또는 예외.
    """
    api_url = (settings.CURRICULUM_GENERATION_API_URL or "").rstrip("/")
    token = (settings.CURRICULUM_GENERATION_API_TOKEN or "").strip()
    if not api_url or not token:
        raise ValueError("CURRICULUM_GENERATION_API_URL or CURRICULUM_GENERATION_API_TOKEN is not set")

    try:
        curriculum = await curriculums.get_curriculum(curriculum_id)
    except Exception as e:
        raise ValueError(f"Failed to get curriculum: {e}")

    paper_id: str | None = None
    paper_title: str = "Paper title"
    paper_authors: list[str] = []
    paper_abstract: str = ""
    keywords: list[str] = []
    extracted_text: str = ""
    
    try:
        # curriculum_id로 연결된 paper 조회
        paper_list, _ = await papers.get_papers_by_curriculum(
            curriculum_id=curriculum_id, page=1, limit=1
        )
        if paper_list:
            paper = paper_list[0]
            paper_id = str(paper.get("id", ""))
            paper_title = str(paper.get("title") or paper_title)
            paper_authors = paper.get("authors") or []
            paper_abstract = paper.get("abstract") or ""
            keywords = paper.get("keywords") or []
            extracted_text = paper.get("extracted_text") or ""
            summary = paper.get("summary") or ""
    except Exception:
        raise ValueError("Failed to get paper")

    # user_info 구조 생성
    budgeted_time = curriculum.get("budgeted_time") or {}
    total_days = str(budgeted_time.get("days", 0))
    hours_per_day = str(budgeted_time.get("daily_hours", 0))
    total_hours = str(int(budgeted_time.get("days", 0)) * float(budgeted_time.get("daily_hours", 0)))
    
    user_info = {
        "purpose": curriculum.get("purpose") or "",
        "level": curriculum.get("level") or "",
        "known_concept": curriculum.get("known_concepts") or [],
        "budgeted_time": {
            "total_days": total_days,
            "hours_per_day": hours_per_day,
            "total_hours": total_hours,
        },
        "resource_type_preference": curriculum.get("preferred_resources") or [],
    }
    
    # paper_content 구조 생성
    # extracted_text가 JSON 형식일 경우 body 필드 추출
    paper_body = []
    if extracted_text:
        try:
            # extracted_text가 JSON 문자열인 경우 파싱
            if isinstance(extracted_text, str):
                parsed_text = json.loads(extracted_text)
                paper_body = parsed_text.get("body", [])
            # 이미 딕셔너리인 경우
            elif isinstance(extracted_text, dict):
                paper_body = extracted_text.get("body", [])
            # 그 외의 경우 원본 텍스트를 그대로 사용
            else:
                paper_body = [
                    {
                        "subtitle": "Full Text",
                        "text": str(extracted_text),
                    }
                ]
        except (json.JSONDecodeError, AttributeError):
            # JSON 파싱 실패 시 원본 텍스트를 그대로 사용
            paper_body = [
                {
                    "subtitle": "Full Text",
                    "text": extracted_text,
                }
            ]
    
    paper_content = {
        "title": paper_title,
        "author": ", ".join(paper_authors) if paper_authors else "",
        "abstract": paper_abstract,
        "body": paper_body,
    }

    keywords_list: list[str] = list(keywords) if isinstance(keywords, list) else []
    body: dict[str, Any] = {
        "curriculum_id": curriculum_id,
        "paper_id": paper_id or "",
        "initial_keyword": keywords_list,
        "paper_summary": summary or "",
        "paper_content": paper_content,
        "user_info": user_info,
        "paper_title": paper_title or "",
        "keywords": keywords_list,
    }

    url = f"{api_url}{CURR_GENERATE_PATH}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    print(headers)
    print(body)
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        return resp.json()


