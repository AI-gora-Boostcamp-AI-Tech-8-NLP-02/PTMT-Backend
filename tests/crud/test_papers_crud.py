from __future__ import annotations

import uuid

import pytest

from app.core.config import settings
from app.crud import papers
from app.crud.errors import NotFoundError


def _skip_if_no_supabase() -> None:
    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
        pytest.skip("Supabase env not configured (SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY).")


@pytest.mark.asyncio
async def test_papers_crud_roundtrip() -> None:
    _skip_if_no_supabase()

    created = await papers.create_paper(
        title=f"Test Paper {uuid.uuid4().hex}",
        authors=["A", "B"],
        abstract="abstract",
        language="english",
        source_url="https://example.com",
        pdf_storage_path="papers/test.pdf",
    )
    paper_id = created["id"]

    try:
        fetched = await papers.get_paper(paper_id)
        assert fetched["id"] == paper_id

        updated = await papers.update_paper(paper_id, title="Updated Title")
        assert updated["title"] == "Updated Title"

        items, total = await papers.list_papers(page=1, limit=50)
        assert total >= 1
        assert any(p["id"] == paper_id for p in items)
    finally:
        await papers.delete_paper(paper_id)

    with pytest.raises(NotFoundError):
        await papers.get_paper(paper_id)

