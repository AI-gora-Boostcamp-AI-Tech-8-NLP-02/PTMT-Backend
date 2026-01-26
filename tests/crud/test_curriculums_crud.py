from __future__ import annotations

import uuid

import pytest

from app.core.config import settings
from app.crud import curriculums
from app.crud.errors import NotFoundError


def _skip_if_no_supabase() -> None:
    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
        pytest.skip("Supabase env not configured (SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY).")


@pytest.mark.asyncio
async def test_curriculums_crud_roundtrip() -> None:
    _skip_if_no_supabase()

    created = await curriculums.create_curriculum(
        title=f"Test Curriculum {uuid.uuid4().hex}",
        status="draft",
        purpose="simple_study",
        level="bachelor",
        known_concepts=["linear_algebra"],
        budgeted_time={"days": 7, "daily_hours": 2},
        preferred_resources=["paper", "article"],
        graph_data={"meta": {"total_nodes": 0}, "nodes": [], "edges": []},
        node_count=0,
        estimated_hours=0.0,
    )
    curriculum_id = created["id"]

    try:
        fetched = await curriculums.get_curriculum(curriculum_id)
        assert fetched["id"] == curriculum_id

        updated = await curriculums.update_curriculum(curriculum_id, status="ready")
        assert updated["status"] == "ready"

        items, total = await curriculums.list_curriculums(page=1, limit=50)
        assert total >= 1
        assert any(c["id"] == curriculum_id for c in items)

        items2, _ = await curriculums.list_curriculums(status="ready", page=1, limit=50)
        assert any(c["id"] == curriculum_id for c in items2)
    finally:
        await curriculums.delete_curriculum(curriculum_id)

    with pytest.raises(NotFoundError):
        await curriculums.get_curriculum(curriculum_id)

