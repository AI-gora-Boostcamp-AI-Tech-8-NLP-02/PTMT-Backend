"""Papers CRUD (Supabase table: papers)."""

from __future__ import annotations

from typing import Any, Optional

from postgrest.exceptions import APIError
from postgrest.types import CountMethod

from .errors import NotFoundError
from . import junctions, users
from .supabase_client import get_supabase_client, translate_postgrest_error


async def create_paper(
    *,
    title: str,
    authors: Optional[list[str]] = None,
    abstract: Optional[str] = None,
    language: str = "english",
    source_url: Optional[str] = None,
    pdf_storage_path: Optional[str] = None,
    extracted_text: Optional[str] = None,
) -> dict[str, Any]:
    client = await get_supabase_client()
    payload: dict[str, Any] = {
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "language": language,
        "source_url": source_url,
        "pdf_storage_path": pdf_storage_path,
        "extracted_text": extracted_text,
    }
    try:
        resp = await client.table("papers").insert(payload).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to create paper") from e

    if not resp.data:
        raise RuntimeError("Supabase insert returned no data for papers")
    return resp.data[0]


async def get_paper(paper_id: str) -> dict[str, Any]:
    client = await get_supabase_client()
    try:
        req = (
            client.table("papers")
            .select("*")
            .eq("id", paper_id)
            .maybe_single()
        )
        resp = await req.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to fetch paper") from e

    if resp is None:
        raise NotFoundError("Paper not found")
    return resp.data


async def get_papers_by_user(
    *,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    """Return (papers, total) linked to a user via user_papers.

    Provide either user_id or email.
    """

    if (user_id is None and email is None) or (user_id is not None and email is not None):
        raise ValueError("Provide exactly one of user_id or email")

    if email is not None:
        user_row = await users.get_user_by_email(email)
        user_id = str(user_row["id"])

    assert user_id is not None
    links, total = await junctions.list_user_papers(user_id=user_id, page=page, limit=limit)
    paper_ids = [str(r["paper_id"]) for r in links]
    if not paper_ids:
        return [], total

    client = await get_supabase_client()
    try:
        resp = await client.table("papers").select("*").in_("id", paper_ids).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to fetch papers by user") from e

    rows = list(resp.data or [])
    by_id = {str(r.get("id")): r for r in rows if isinstance(r, dict)}
    ordered = [by_id[pid] for pid in paper_ids if pid in by_id]
    return ordered, total


async def get_paper_by_user(
    *, user_id: Optional[str] = None, email: Optional[str] = None, page: int = 1, limit: int = 50
) -> tuple[list[dict[str, Any]], int]:
    """Alias for get_papers_by_user (returns a list)."""

    return await get_papers_by_user(user_id=user_id, email=email, page=page, limit=limit)


async def get_papers_by_curriculum(
    *, curriculum_id: str, page: int = 1, limit: int = 50
) -> tuple[list[dict[str, Any]], int]:
    """Return (papers, total) linked to a curriculum via curriculum_papers."""

    links, total = await junctions.list_curriculum_papers(
        curriculum_id=curriculum_id, page=page, limit=limit
    )
    paper_ids = [str(r["paper_id"]) for r in links]
    if not paper_ids:
        return [], total

    client = await get_supabase_client()
    try:
        resp = await client.table("papers").select("*").in_("id", paper_ids).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to fetch papers by curriculum") from e

    rows = list(resp.data or [])
    by_id = {str(r.get("id")): r for r in rows if isinstance(r, dict)}
    ordered = [by_id[pid] for pid in paper_ids if pid in by_id]
    return ordered, total


async def get_paper_by_curr(
    *, curriculum_id: str, page: int = 1, limit: int = 50
) -> tuple[list[dict[str, Any]], int]:
    """Alias for get_papers_by_curriculum (returns a list)."""

    return await get_papers_by_curriculum(curriculum_id=curriculum_id, page=page, limit=limit)


async def list_papers(*, page: int = 1, limit: int = 20) -> tuple[list[dict[str, Any]], int]:
    """Return (items, total)."""

    if page < 1:
        raise ValueError("page must be >= 1")
    if limit < 1:
        raise ValueError("limit must be >= 1")

    client = await get_supabase_client()
    offset = (page - 1) * limit
    try:
        resp = (
            client.table("papers")
            .select("*", count=CountMethod.exact)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        resp = await resp.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to list papers") from e

    total = int(resp.count or 0)
    return list(resp.data or []), total


async def update_paper(paper_id: str, **fields: Any) -> dict[str, Any]:
    client = await get_supabase_client()
    if not fields:
        return await get_paper(paper_id)
    try:
        resp = await client.table("papers").update(fields).eq("id", paper_id).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to update paper") from e

    if resp.data:
        return resp.data[0]
    return await get_paper(paper_id)


async def delete_paper(paper_id: str) -> None:
    _ = await get_paper(paper_id)
    client = await get_supabase_client()
    try:
        resp = await client.table("papers").delete().eq("id", paper_id).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to delete paper") from e
    _ = resp

