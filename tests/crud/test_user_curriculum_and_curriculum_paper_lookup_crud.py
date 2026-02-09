from __future__ import annotations

import uuid

import pytest

from app.core.config import settings
from app.crud import curriculums, junctions, papers, users


def _skip_if_no_supabase() -> None:
    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
        pytest.skip("Supabase env not configured (SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY).")


@pytest.mark.asyncio
async def test_user_curriculum_lookup_helpers() -> None:
    _skip_if_no_supabase()

    email = f"test-{uuid.uuid4().hex}@example.com"
    user = await users.create_user(email=email, password_hash="hash", name="UC Lookup User")
    user_id = str(user["id"])

    c1 = await curriculums.create_curriculum(title=f"UC1 {uuid.uuid4().hex}")
    c2 = await curriculums.create_curriculum(title=f"UC2 {uuid.uuid4().hex}")
    curr_id_1 = str(c1["id"])
    curr_id_2 = str(c2["id"])

    try:
        await junctions.add_user_curriculum(user_id=user_id, curriculum_id=curr_id_1)
        await junctions.add_user_curriculum(user_id=user_id, curriculum_id=curr_id_2)

        by_user, total = await curriculums.get_curr_by_user(user_id=user_id, page=1, limit=50)
        assert total >= 2
        ids = {c["id"] for c in by_user}
        assert curr_id_1 in ids and curr_id_2 in ids

        by_email, total2 = await curriculums.get_curr_by_user(email=email, page=1, limit=50)
        assert total2 == total

        linked_users, utotal = await users.get_user_by_curr(curriculum_id=curr_id_1, page=1, limit=50)
        assert utotal >= 1
        assert any(u["id"] == user_id for u in linked_users)
    finally:
        await curriculums.delete_curriculum(curr_id_1)
        await curriculums.delete_curriculum(curr_id_2)
        await users.delete_user(user_id)


@pytest.mark.asyncio
async def test_curriculum_paper_lookup_helpers() -> None:
    _skip_if_no_supabase()

    paper = await papers.create_paper(title=f"CP Paper {uuid.uuid4().hex}")
    curriculum = await curriculums.create_curriculum(title=f"CP Curriculum {uuid.uuid4().hex}")
    paper_id = str(paper["id"])
    curriculum_id = str(curriculum["id"])

    try:
        await junctions.add_curriculum_paper(curriculum_id=curriculum_id, paper_id=paper_id)

        currs, total = await curriculums.get_curr_by_paper(paper_id=paper_id, page=1, limit=50)
        assert total >= 1
        assert any(c["id"] == curriculum_id for c in currs)

        ps, ptotal = await papers.get_paper_by_curr(curriculum_id=curriculum_id, page=1, limit=50)
        assert ptotal >= 1
        assert any(p["id"] == paper_id for p in ps)
    finally:
        await curriculums.delete_curriculum(curriculum_id)
        await papers.delete_paper(paper_id)

