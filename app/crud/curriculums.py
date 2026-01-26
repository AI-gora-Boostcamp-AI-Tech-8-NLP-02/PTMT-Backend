"""Curriculums CRUD (Supabase table: curriculums)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from postgrest.exceptions import APIError
from postgrest.types import CountMethod

from .errors import NotFoundError
from . import junctions, users
from .supabase_client import get_supabase_client, translate_postgrest_error


async def create_curriculum(
    *,
    title: Optional[str] = None,
    status: str = "draft",
    purpose: Optional[str] = None,
    level: Optional[str] = None,
    known_concepts: Optional[list[str]] = None,
    budgeted_time: Optional[dict[str, Any]] = None,
    preferred_resources: Optional[list[str]] = None,
    graph_data: Optional[dict[str, Any]] = None,
    node_count: int = 0,
    estimated_hours: float = 0.0,
) -> dict[str, Any]:
    client = await get_supabase_client()
    payload: dict[str, Any] = {
        "title": title,
        "status": status,
        "purpose": purpose,
        "level": level,
        "known_concepts": known_concepts,
        "budgeted_time": budgeted_time,
        "preferred_resources": preferred_resources,
        "graph_data": graph_data,
        "node_count": node_count,
        "estimated_hours": estimated_hours,
    }
    try:
        resp = await client.table("curriculums").insert(payload).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to create curriculum") from e

    if not resp.data:
        raise RuntimeError("Supabase insert returned no data for curriculums")
    return resp.data[0]


async def get_curriculum(curriculum_id: str) -> dict[str, Any]:
    client = await get_supabase_client()
    try:
        resp = (
            client.table("curriculums")
            .select("*")
            .eq("id", curriculum_id)
            .maybe_single()
        )
        resp = await resp.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to fetch curriculum") from e

    if resp is None:
        raise NotFoundError("Curriculum not found")
    return resp.data


async def get_curriculums_by_user(
    *,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    """Return (curriculums, total) linked to a user via user_curriculums.

    Provide either user_id or email.
    """

    if (user_id is None and email is None) or (user_id is not None and email is not None):
        raise ValueError("Provide exactly one of user_id or email")

    if email is not None:
        user_row = await users.get_user_by_email(email)
        user_id = str(user_row["id"])

    assert user_id is not None
    links, total = await junctions.list_user_curriculums(
        user_id=user_id, page=page, limit=limit
    )
    curriculum_ids = [str(r["curriculum_id"]) for r in links]
    if not curriculum_ids:
        return [], total

    client = await get_supabase_client()
    try:
        resp = client.table("curriculums").select("*").in_("id", curriculum_ids)
        resp = await resp.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to fetch curriculums by user") from e

    rows = list(resp.data or [])
    by_id = {str(r.get("id")): r for r in rows if isinstance(r, dict)}
    ordered = [by_id[cid] for cid in curriculum_ids if cid in by_id]
    return ordered, total


async def get_curr_by_user(
    *,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    """Alias for get_curriculums_by_user (returns a list)."""

    return await get_curriculums_by_user(
        user_id=user_id, email=email, page=page, limit=limit
    )


async def get_curriculums_by_paper(
    *, paper_id: str, page: int = 1, limit: int = 50
) -> tuple[list[dict[str, Any]], int]:
    """Return (curriculums, total) linked to a paper via curriculum_papers."""

    links, total = await junctions.list_paper_curriculums(
        paper_id=paper_id, page=page, limit=limit
    )
    curriculum_ids = [str(r["curriculum_id"]) for r in links]
    if not curriculum_ids:
        return [], total

    client = await get_supabase_client()
    try:
        resp = client.table("curriculums").select("*").in_("id", curriculum_ids)
        resp = await resp.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to fetch curriculums by paper") from e

    rows = list(resp.data or [])
    by_id = {str(r.get("id")): r for r in rows if isinstance(r, dict)}
    ordered = [by_id[cid] for cid in curriculum_ids if cid in by_id]
    return ordered, total


async def get_curr_by_paper(
    *, paper_id: str, page: int = 1, limit: int = 50
) -> tuple[list[dict[str, Any]], int]:
    """Alias for get_curriculums_by_paper (returns a list)."""

    return await get_curriculums_by_paper(paper_id=paper_id, page=page, limit=limit)


async def has_curriculum_for_paper(*, paper_id: str) -> bool:
    """Return True if any curriculum is linked to the given paper.

    Uses the `curriculum_papers` junction table (fast existence check).
    """

    _rows, total = await junctions.list_paper_curriculums(paper_id=paper_id, page=1, limit=1)
    return total > 0


def _norm_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        # Treat as order-insensitive set of strings.
        return sorted([str(v) for v in value])
    return [str(value)]


def _norm_json(value: Any) -> Any:
    # For budgeted_time stored as JSONB; compare structurally.
    return value if value is not None else None


async def find_curriculum_by_paper_and_options(
    *,
    paper_id: str,
    purpose: Optional[str],
    level: Optional[str],
    known_concepts: Optional[list[str]],
    budgeted_time: Optional[dict[str, Any]],
    preferred_resources: Optional[list[str]],
    limit: int = 200,
) -> Optional[dict[str, Any]]:
    """Find an existing curriculum linked to paper with identical options.

    Matching keys:
    - paper_id via `curriculum_papers`
    - purpose, level, known_concepts, budgeted_time, preferred_resources on `curriculums`

    Notes:
    - `known_concepts` / `preferred_resources` are compared order-insensitively.
    - Returns the most recently created matching curriculum when multiple exist.
    """

    links, _total = await junctions.list_paper_curriculums(paper_id=paper_id, page=1, limit=limit)
    curriculum_ids = [str(r["curriculum_id"]) for r in links]
    if not curriculum_ids:
        return None

    client = await get_supabase_client()
    try:
        req = client.table("curriculums").select("*").in_("id", curriculum_ids)
        resp = await req.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to fetch curriculums for paper") from e

    rows = [r for r in (resp.data or []) if isinstance(r, dict)]
    rows.sort(key=lambda r: str(r.get("created_at", "")), reverse=True)

    target_known = _norm_list(known_concepts)
    target_pref = _norm_list(preferred_resources)
    target_budget = _norm_json(budgeted_time)

    for row in rows:
        if row.get("purpose") != purpose:
            continue
        if row.get("level") != level:
            continue
        if _norm_list(row.get("known_concepts")) != target_known:
            continue
        if _norm_list(row.get("preferred_resources")) != target_pref:
            continue
        if _norm_json(row.get("budgeted_time")) != target_budget:
            continue
        return row

    return None


async def list_curriculums(
    *, status: Optional[str] = None, page: int = 1, limit: int = 20
) -> tuple[list[dict[str, Any]], int]:
    """Return (items, total)."""

    if page < 1:
        raise ValueError("page must be >= 1")
    if limit < 1:
        raise ValueError("limit must be >= 1")

    client = await get_supabase_client()
    offset = (page - 1) * limit
    try:
        q = (
            client.table("curriculums")
            .select("*", count=CountMethod.exact)
            .order("created_at", desc=True)
        )
        if status:
            q = q.eq("status", status)
        resp = await q.range(offset, offset + limit - 1).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to list curriculums") from e

    total = int(resp.count or 0)
    return list(resp.data or []), total


async def update_curriculum(curriculum_id: str, **fields: Any) -> dict[str, Any]:
    client = await get_supabase_client()
    if not fields:
        return await get_curriculum(curriculum_id)
    fields.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
    try:
        resp = await client.table("curriculums").update(fields).eq("id", curriculum_id).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to update curriculum") from e

    if resp.data:
        return resp.data[0]
    return await get_curriculum(curriculum_id)


async def delete_curriculum(curriculum_id: str) -> None:
    _ = await get_curriculum(curriculum_id)
    client = await get_supabase_client()
    try:
        resp = await client.table("curriculums").delete().eq("id", curriculum_id).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to delete curriculum") from e
    _ = resp

