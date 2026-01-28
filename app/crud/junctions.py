"""Junction table CRUD.

DDL junction tables:
- user_papers(user_id, paper_id)
- user_curriculums(user_id, curriculum_id)
- curriculum_papers(curriculum_id, paper_id)
"""

from __future__ import annotations

from typing import Any

from postgrest.exceptions import APIError
from postgrest.types import CountMethod

from .errors import NotFoundError
from .supabase_client import get_supabase_client, translate_postgrest_error


# -----------------------
# user_papers
# -----------------------


async def add_user_paper(*, user_id: str, paper_id: str) -> dict[str, Any]:
    client = await get_supabase_client()
    try:
        resp = await client.table("user_papers").insert({"user_id": user_id, "paper_id": paper_id}).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to link user_paper") from e
    if not resp.data:
        raise RuntimeError("Supabase insert returned no data for user_papers")
    return resp.data[0]


async def remove_user_paper(*, user_id: str, paper_id: str) -> None:
    client = await get_supabase_client()
    # Ensure NotFound semantics even if delete returns minimal body.
    try:
        exists = (
            client.table("user_papers")
            .select("*")
            .eq("user_id", user_id)
            .eq("paper_id", paper_id)
            .maybe_single()
        )
        exists = await exists.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to check user_papers link") from e
    if exists is None:
        raise NotFoundError("user_papers link not found")
    try:
        resp = (
            client.table("user_papers")
            .delete()
            .eq("user_id", user_id)
            .eq("paper_id", paper_id)
        )
        resp = await resp.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to unlink user_paper") from e
    _ = resp


async def list_user_papers(*, user_id: str, page: int = 1, limit: int = 50) -> tuple[list[dict[str, Any]], int]:
    if page < 1:
        raise ValueError("page must be >= 1")
    if limit < 1:
        raise ValueError("limit must be >= 1")
    client = await get_supabase_client()
    offset = (page - 1) * limit
    try:
        resp = (
            client.table("user_papers")
            .select("*", count=CountMethod.exact)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        resp = await resp.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to list user_papers") from e
    return list(resp.data or []), int(resp.count or 0)


async def list_paper_users(
    *, paper_id: str, page: int = 1, limit: int = 50
) -> tuple[list[dict[str, Any]], int]:
    """List user_papers rows for a given paper_id."""

    if page < 1:
        raise ValueError("page must be >= 1")
    if limit < 1:
        raise ValueError("limit must be >= 1")
    client = await get_supabase_client()
    offset = (page - 1) * limit
    try:
        resp = (
            client.table("user_papers")
            .select("*", count=CountMethod.exact)
            .eq("paper_id", paper_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        resp = await resp.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to list paper_users") from e
    return list(resp.data or []), int(resp.count or 0)


# -----------------------
# user_curriculums
# -----------------------


async def add_user_curriculum(*, user_id: str, curriculum_id: str) -> dict[str, Any]:
    client = await get_supabase_client()
    try:
        resp = await client.table("user_curriculums").insert({"user_id": user_id, "curriculum_id": curriculum_id}).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to link user_curriculum") from e
    if not resp.data:
        raise RuntimeError("Supabase insert returned no data for user_curriculums")
    return resp.data[0]


async def remove_user_curriculum(*, user_id: str, curriculum_id: str) -> None:
    client = await get_supabase_client()
    try:
        exists = (
            client.table("user_curriculums")
            .select("*")
            .eq("user_id", user_id)
            .eq("curriculum_id", curriculum_id)
            .maybe_single()
        )
        exists = await exists.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to check user_curriculums link") from e
    if exists is None:
        raise NotFoundError("user_curriculums link not found")
    try:
        resp = (
            client.table("user_curriculums")
            .delete()
            .eq("user_id", user_id)
            .eq("curriculum_id", curriculum_id)
        )
        resp = await resp.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to unlink user_curriculum") from e
    _ = resp


async def list_user_curriculums(
    *, user_id: str, page: int = 1, limit: int = 50
) -> tuple[list[dict[str, Any]], int]:
    if page < 1:
        raise ValueError("page must be >= 1")
    if limit < 1:
        raise ValueError("limit must be >= 1")
    client = await get_supabase_client()
    offset = (page - 1) * limit
    try:
        resp = (
            client.table("user_curriculums")
            .select("*", count=CountMethod.exact)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        resp = await resp.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to list user_curriculums") from e
    return list(resp.data or []), int(resp.count or 0)


async def list_curriculum_users(
    *, curriculum_id: str, page: int = 1, limit: int = 50
) -> tuple[list[dict[str, Any]], int]:
    """List user_curriculums rows for a given curriculum_id."""

    if page < 1:
        raise ValueError("page must be >= 1")
    if limit < 1:
        raise ValueError("limit must be >= 1")
    client = await get_supabase_client()
    offset = (page - 1) * limit
    try:
        resp = (
            client.table("user_curriculums")
            .select("*", count=CountMethod.exact)
            .eq("curriculum_id", curriculum_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        resp = await resp.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to list curriculum_users") from e
    return list(resp.data or []), int(resp.count or 0)


# -----------------------
# curriculum_papers
# -----------------------


async def add_curriculum_paper(*, curriculum_id: str, paper_id: str) -> dict[str, Any]:
    client = await get_supabase_client()
    try:
        resp = await client.table("curriculum_papers").insert({"curriculum_id": curriculum_id, "paper_id": paper_id}).execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to link curriculum_paper") from e
    if not resp.data:
        raise RuntimeError("Supabase insert returned no data for curriculum_papers")
    return resp.data[0]


async def remove_curriculum_paper(*, curriculum_id: str, paper_id: str) -> None:
    client = await get_supabase_client()
    try:
        exists = (
            client.table("curriculum_papers")
            .select("*")
            .eq("curriculum_id", curriculum_id)
            .eq("paper_id", paper_id)
            .maybe_single()
        )
        exists = await exists.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to check curriculum_papers link") from e
    if exists is None:
        raise NotFoundError("curriculum_papers link not found")
    try:
        resp = (
            client.table("curriculum_papers")
            .delete()
            .eq("curriculum_id", curriculum_id)
            .eq("paper_id", paper_id)
        )
        resp = await resp.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to unlink curriculum_paper") from e
    _ = resp


async def list_curriculum_papers(
    *, curriculum_id: str, page: int = 1, limit: int = 50
) -> tuple[list[dict[str, Any]], int]:
    if page < 1:
        raise ValueError("page must be >= 1")
    if limit < 1:
        raise ValueError("limit must be >= 1")
    client = await get_supabase_client()
    offset = (page - 1) * limit
    try:
        resp = (
            client.table("curriculum_papers")
            .select("*", count=CountMethod.exact)
            .eq("curriculum_id", curriculum_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        resp = await resp.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to list curriculum_papers") from e
    return list(resp.data or []), int(resp.count or 0)


async def list_paper_curriculums(
    *, paper_id: str, page: int = 1, limit: int = 50
) -> tuple[list[dict[str, Any]], int]:
    """List curriculum_papers rows for a given paper_id."""

    if page < 1:
        raise ValueError("page must be >= 1")
    if limit < 1:
        raise ValueError("limit must be >= 1")
    client = await get_supabase_client()
    offset = (page - 1) * limit
    try:
        resp = (
            client.table("curriculum_papers")
            .select("*", count=CountMethod.exact)
            .eq("paper_id", paper_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        resp = await resp.execute()
    except APIError as e:
        raise translate_postgrest_error(e, default_message="Failed to list paper_curriculums") from e
    return list(resp.data or []), int(resp.count or 0)

