"""arXiv API로 논문 검색 후, query와 유사도가 가장 높은 결과의 PDF URL 반환."""

from __future__ import annotations

import asyncio
import re
from difflib import SequenceMatcher
from typing import Any

import arxiv

_ARXIV_MAX_RESULTS = 20


def _normalize_text(text: str) -> str:
    """공백 정규화 후 소문자."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip().lower())


def _similarity(query_norm: str, title: str) -> float:
    """query와 title 문자열 유사도 0~1."""
    title_norm = _normalize_text(title)
    if not query_norm or not title_norm:
        return 0.0
    return SequenceMatcher(None, query_norm, title_norm).ratio()


def _search_arxiv_and_pick_best(query: str, max_results: int = 5) -> dict[str, Any] | None:
    """동기: arXiv 검색 후 최대 max_results개 수집, query와 유사도가 가장 높은 하나 반환."""
    if not (query or str(query).strip()):
        return None
    q = query.strip()
    query_norm = _normalize_text(q)
    client = arxiv.Client()
    search = arxiv.Search(query=q, max_results=max_results)
    candidates: list[dict[str, Any]] = []
    try:
        for r in client.results(search):
            if not r.pdf_url:
                continue
            source_url = r.entry_id or f"https://arxiv.org/abs/{r.get_short_id()}"
            title = r.title or ""
            score = _similarity(query_norm, title)
            candidates.append({
                "pdf_url": r.pdf_url,
                "source_url": source_url,
                "title": title,
                "_score": score,
            })
            if len(candidates) >= max_results:
                break
    except Exception:
        pass
    if not candidates:
        return None
    best = max(candidates, key=lambda x: x["_score"])
    del best["_score"]
    return best


async def search_arxiv_first_pdf(query: str) -> dict[str, Any] | None:
    """arXiv 검색 5건 중 query와 유사도가 가장 높은 논문의 PDF URL·소스 URL·제목 반환. 없으면 None."""
    return await asyncio.to_thread(_search_arxiv_and_pick_best, query, _ARXIV_MAX_RESULTS)
