from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.crud import refresh_tokens, users


def _skip_if_no_supabase() -> None:
    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
        pytest.skip("Supabase env not configured (SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY).")


@pytest.mark.asyncio
async def test_refresh_tokens_crud() -> None:
    _skip_if_no_supabase()

    user = await users.create_user(
        email=f"test-{uuid.uuid4().hex}@example.com",
        password_hash="hash",
        name="Token User",
    )
    user_id = user["id"]

    token_id: str | None = None
    try:
        token = await refresh_tokens.create_refresh_token(
            user_id=user_id,
            token_hash=f"hash-{uuid.uuid4().hex}",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        token_id = token["id"]

        rows, total = await refresh_tokens.list_user_refresh_tokens(user_id, page=1, limit=50)
        assert total >= 1
        assert any(r["id"] == token_id for r in rows)

        revoked = await refresh_tokens.revoke_refresh_token(token_id)
        assert revoked["revoked_at"] is not None
    finally:
        # Deleting user cascades refresh_tokens
        await users.delete_user(user_id)

