"""Refresh token CRUD (Supabase table: refresh_tokens)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from postgrest.exceptions import APIError
from postgrest.types import CountMethod

from .errors import NotFoundError
from .supabase_client import get_supabase_client, translate_postgrest_error


async def create_refresh_token(
    *,
    user_id: str,
    token_hash: str,
    expires_at: datetime,
) -> dict[str, Any]:
    client = await get_supabase_client()
    payload: dict[str, Any] = {
        "user_id": user_id,
        "token_hash": token_hash,
        "expires_at": expires_at.isoformat(),
    }
    try:
        resp = await client.table("refresh_tokens").insert(payload).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to create refresh token") from e

    if not resp.data:
        raise RuntimeError("Supabase insert returned no data for refresh_tokens")
    return resp.data[0]


async def revoke_refresh_token(token_id: str, *, revoked_at: Optional[datetime] = None) -> dict[str, Any]:
    client = await get_supabase_client()
    revoked_at = revoked_at or datetime.now(timezone.utc)
    try:
        resp = (
            client.table("refresh_tokens")
            .update({"revoked_at": revoked_at.isoformat()})
            .eq("id", token_id)
        )
        resp = await resp.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to revoke refresh token") from e

    if resp.data:
        return resp.data[0]
    # Fallback if update returns minimal response body.
    try:
        check = (
            client.table("refresh_tokens").select("*").eq("id", token_id).maybe_single()
        )
        check = await check.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to fetch refresh token") from e
    if check is None:
        raise NotFoundError("Refresh token not found")
    return check.data


async def list_user_refresh_tokens(
    user_id: str, *, page: int = 1, limit: int = 50
) -> tuple[list[dict[str, Any]], int]:
    if page < 1:
        raise ValueError("page must be >= 1")
    if limit < 1:
        raise ValueError("limit must be >= 1")

    client = await get_supabase_client()
    offset = (page - 1) * limit
    try:
        resp = (
            client.table("refresh_tokens")
            .select("*", count=CountMethod.exact)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        resp = await resp.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to list refresh tokens") from e

    total = int(resp.count or 0)
    return list(resp.data or []), total

