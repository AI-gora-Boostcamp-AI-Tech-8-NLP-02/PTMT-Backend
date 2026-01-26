from __future__ import annotations

import uuid

import pytest

from app.core.config import settings
from app.crud import junctions, papers, users


def _skip_if_no_supabase() -> None:
    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
        pytest.skip("Supabase env not configured (SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY).")


@pytest.mark.asyncio
async def test_user_paper_lookup_helpers() -> None:
    _skip_if_no_supabase()

    email = f"test-{uuid.uuid4().hex}@example.com"
    user = await users.create_user(email=email, password_hash="hash", name="Lookup User")
    user_id = user["id"]

    p1 = await papers.create_paper(title=f"Lookup Paper 1 {uuid.uuid4().hex}")
    p2 = await papers.create_paper(title=f"Lookup Paper 2 {uuid.uuid4().hex}")
    paper_id_1 = p1["id"]
    paper_id_2 = p2["id"]

    try:
        await junctions.add_user_paper(user_id=user_id, paper_id=paper_id_1)
        await junctions.add_user_paper(user_id=user_id, paper_id=paper_id_2)

        by_user, total = await papers.get_paper_by_user(user_id=str(user_id), page=1, limit=50)
        assert total >= 2
        ids = {p["id"] for p in by_user}
        assert str(paper_id_1) in ids
        assert str(paper_id_2) in ids

        by_email, total2 = await papers.get_paper_by_user(email=email, page=1, limit=50)
        assert total2 == total
        ids2 = {p["id"] for p in by_email}
        assert str(paper_id_1) in ids2

        linked_users, utotal = await users.get_user_by_paper(paper_id=str(paper_id_1), page=1, limit=50)
        assert utotal >= 1
        assert any(u["id"] == str(user_id) for u in linked_users)
    finally:
        # Base record cleanup (FK on junctions is ON DELETE CASCADE for users/papers)
        await papers.delete_paper(str(paper_id_1))
        await papers.delete_paper(str(paper_id_2))
        await users.delete_user(str(user_id))

