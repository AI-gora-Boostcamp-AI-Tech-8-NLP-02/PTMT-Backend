from __future__ import annotations

import uuid

import pytest

from app.core.config import settings
from app.crud import curriculums, junctions, papers, users


def _skip_if_no_supabase() -> None:
    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
        pytest.skip("Supabase env not configured (SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY).")


@pytest.mark.asyncio
async def test_junctions_linking() -> None:
    _skip_if_no_supabase()

    user = await users.create_user(
        email=f"test-{uuid.uuid4().hex}@example.com",
        password_hash="hash",
        name="Junction User",
    )
    paper = await papers.create_paper(title=f"Junction Paper {uuid.uuid4().hex}")
    curriculum = await curriculums.create_curriculum(title=f"Junction Curriculum {uuid.uuid4().hex}")

    user_id = user["id"]
    paper_id = paper["id"]
    curriculum_id = curriculum["id"]

    try:
        await junctions.add_user_paper(user_id=user_id, paper_id=paper_id)
        await junctions.add_user_curriculum(user_id=user_id, curriculum_id=curriculum_id)
        await junctions.add_curriculum_paper(curriculum_id=curriculum_id, paper_id=paper_id)

        up_rows, _ = await junctions.list_user_papers(user_id=user_id, page=1, limit=50)
        assert any(r["paper_id"] == paper_id for r in up_rows)

        uc_rows, _ = await junctions.list_user_curriculums(user_id=user_id, page=1, limit=50)
        assert any(r["curriculum_id"] == curriculum_id for r in uc_rows)

        cp_rows, _ = await junctions.list_curriculum_papers(curriculum_id=curriculum_id, page=1, limit=50)
        assert any(r["paper_id"] == paper_id for r in cp_rows)

        # Unlink
        await junctions.remove_curriculum_paper(curriculum_id=curriculum_id, paper_id=paper_id)
        await junctions.remove_user_curriculum(user_id=user_id, curriculum_id=curriculum_id)
        await junctions.remove_user_paper(user_id=user_id, paper_id=paper_id)
    finally:
        # Cleanup base records
        await curriculums.delete_curriculum(curriculum_id)
        await papers.delete_paper(paper_id)
        await users.delete_user(user_id)

