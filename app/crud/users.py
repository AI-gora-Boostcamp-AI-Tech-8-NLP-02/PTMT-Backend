"""Users CRUD (Supabase table: users)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from postgrest.exceptions import APIError

from .errors import NotFoundError
from . import junctions
from .supabase_client import get_supabase_client, translate_postgrest_error


async def create_user(
    *,
    email: str,
    password_hash: str,
    name: str,
    avatar_url: Optional[str] = None,
    role: str = "user",
) -> dict[str, Any]:
    client = await get_supabase_client()
    payload: dict[str, Any] = {
        "email": email,
        "password_hash": password_hash,
        "name": name,
        "avatar_url": avatar_url,
        "role": role,
    }
    try:
        resp = await client.table("users").insert(payload).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to create user") from e

    rows = resp.data
    if not rows:
        # With PostgREST, insert should return inserted rows by default.
        raise RuntimeError("Supabase insert returned no data for users")
    return rows[0]


async def get_user(user_id: str) -> dict[str, Any]:
    client = await get_supabase_client()
    try:
        req = client.table("users").select("*").eq("id", user_id).maybe_single()
        resp = await req.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to fetch user") from e

    if resp is None:
        raise NotFoundError("User not found")
    return resp.data


async def get_user_by_email(email: str) -> dict[str, Any]:
    client = await get_supabase_client()
    try:
        req = client.table("users").select("*").eq("email", email).maybe_single()
        resp = await req.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to fetch user by email") from e

    if resp is None:
        raise NotFoundError("User not found")
    return resp.data


async def get_users_by_paper(
    *, paper_id: str, page: int = 1, limit: int = 50
) -> tuple[list[dict[str, Any]], int]:
    """Return (users, total) linked to a paper via user_papers."""

    links, total = await junctions.list_paper_users(
        paper_id=paper_id, page=page, limit=limit
    )
    user_ids = [str(r["user_id"]) for r in links]
    if not user_ids:
        return [], total

    client = await get_supabase_client()
    try:
        resp = await client.table("users").select("*").in_("id", user_ids).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to fetch users by paper") from e

    rows = list(resp.data or [])
    by_id = {str(r.get("id")): r for r in rows if isinstance(r, dict)}
    ordered = [by_id[uid] for uid in user_ids if uid in by_id]
    return ordered, total


async def get_user_by_paper(
    *, paper_id: str, page: int = 1, limit: int = 50
) -> tuple[list[dict[str, Any]], int]:
    """Alias for get_users_by_paper (returns a list)."""

    return await get_users_by_paper(paper_id=paper_id, page=page, limit=limit)


async def get_users_by_curriculum(
    *, curriculum_id: str, page: int = 1, limit: int = 50
) -> tuple[list[dict[str, Any]], int]:
    """Return (users, total) linked to a curriculum via user_curriculums."""

    links, total = await junctions.list_curriculum_users(
        curriculum_id=curriculum_id, page=page, limit=limit
    )
    user_ids = [str(r["user_id"]) for r in links]
    if not user_ids:
        return [], total

    client = await get_supabase_client()
    try:
        resp = await client.table("users").select("*").in_("id", user_ids).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to fetch users by curriculum") from e

    rows = list(resp.data or [])
    by_id = {str(r.get("id")): r for r in rows if isinstance(r, dict)}
    ordered = [by_id[uid] for uid in user_ids if uid in by_id]
    return ordered, total


async def get_user_by_curr(
    *, curriculum_id: str, page: int = 1, limit: int = 50
) -> tuple[list[dict[str, Any]], int]:
    """Alias for get_users_by_curriculum (returns a list)."""

    return await get_users_by_curriculum(
        curriculum_id=curriculum_id, page=page, limit=limit
    )


async def update_user(user_id: str, **fields: Any) -> dict[str, Any]:
    client = await get_supabase_client()
    if not fields:
        return await get_user(user_id)
    # Keep updated_at in sync if caller didn't set it
    fields.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
    try:
        resp = await client.table("users").update(fields).eq("id", user_id).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to update user") from e

    if resp.data:
        return resp.data[0]
    # Some PostgREST configs return minimal bodies; fall back to fetch.
    return await get_user(user_id)


async def delete_user(user_id: str) -> None:
    # Ensure proper NotFound semantics even if delete returns minimal response body.
    _ = await get_user(user_id)
    client = await get_supabase_client()
    try:
        resp = await client.table("users").delete().eq("id", user_id).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to delete user") from e
    # If delete returns representation, resp.data will contain deleted rows.
    _ = resp

