from __future__ import annotations

import uuid

import pytest

from app.core.config import settings
from app.crud import users
from app.crud.errors import NotFoundError


def _skip_if_no_supabase() -> None:
    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
        pytest.skip("Supabase env not configured (SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY).")


@pytest.mark.asyncio
async def test_users_crud_roundtrip() -> None:
    _skip_if_no_supabase()

    email = f"test-{uuid.uuid4().hex}@example.com"
    created = await users.create_user(
        email=email,
        password_hash="hash",
        name="Test User",
    )
    user_id = created["id"]

    try:
        fetched = await users.get_user(user_id)
        assert fetched["email"] == email

        fetched2 = await users.get_user_by_email(email)
        assert fetched2["id"] == user_id

        updated = await users.update_user(user_id, name="Updated Name")
        assert updated["name"] == "Updated Name"
    finally:
        # Cleanup
        await users.delete_user(user_id)

    with pytest.raises(NotFoundError):
        await users.get_user(user_id)
