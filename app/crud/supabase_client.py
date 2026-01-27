"""Supabase client wrapper for CRUD layer.

Uses the service role key by default (server-side).
"""

from __future__ import annotations

import asyncio
import weakref
from typing import Any, Optional

import httpx
from postgrest.exceptions import APIError
from supabase import AsyncClient, acreate_client
from supabase.lib.client_options import AsyncClientOptions

from app.core.config import settings

from .errors import ConflictError, CrudConfigError, ExternalServiceError


def require_supabase_config() -> tuple[str, str]:
    """Return (url, key) or raise if missing.

    We default to the service role key for server-side CRUD.
    """

    url = (settings.SUPABASE_URL or "").strip()
    key = (settings.SUPABASE_SERVICE_ROLE_KEY or "").strip()
    if not url:
        raise CrudConfigError("SUPABASE_URL is not configured.")
    if not key:
        raise CrudConfigError("SUPABASE_SERVICE_ROLE_KEY is not configured.")
    return url, key


def require_supabase_auth_config() -> tuple[str, str]:
    """Return (url, anon_key) for Auth operations.

    Auth operations use the anon key, not the service role key.
    """

    url = (settings.SUPABASE_URL or "").strip()
    key = (settings.SUPABASE_ANON_KEY or "").strip()
    if not url:
        raise CrudConfigError("SUPABASE_URL is not configured.")
    if not key:
        raise CrudConfigError("SUPABASE_ANON_KEY is not configured.")
    return url, key


_clients_by_loop: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, AsyncClient]" = (
    weakref.WeakKeyDictionary()
)
_locks_by_loop: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Lock]" = (
    weakref.WeakKeyDictionary()
)

_auth_clients_by_loop: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, AsyncClient]" = (
    weakref.WeakKeyDictionary()
)
_auth_locks_by_loop: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Lock]" = (
    weakref.WeakKeyDictionary()
)


async def get_supabase_client() -> AsyncClient:
    """Create and cache an async Supabase client instance.

    Cache is per-event-loop to avoid reusing an async HTTP client across
    different loops (common in test runners).

    Uses the service role key for server-side CRUD operations.
    """

    loop = asyncio.get_running_loop()
    existing = _clients_by_loop.get(loop)
    if existing is not None:
        return existing

    lock = _locks_by_loop.get(loop)
    if lock is None:
        lock = asyncio.Lock()
        _locks_by_loop[loop] = lock

    async with lock:
        existing = _clients_by_loop.get(loop)
        if existing is not None:
            return existing
        url, key = require_supabase_config()
        # 타임아웃 설정: PostgREST 타임아웃을 60초로 설정
        timeout = httpx.Timeout(connect=30.0, read=30.0, write=30.0, pool=60.0)
        options = AsyncClientOptions(
            postgrest_client_timeout=timeout,
            httpx_client=httpx.AsyncClient(timeout=timeout)
        )
        client = await acreate_client(url, key, options=options)
        _clients_by_loop[loop] = client
        return client


async def get_supabase_auth_client() -> AsyncClient:
    """Create and cache an async Supabase client instance for Auth operations.

    Uses the anon key (not service role key) for client-side Auth operations.
    Cache is per-event-loop to avoid reusing an async HTTP client across
    different loops (common in test runners).
    """

    loop = asyncio.get_running_loop()
    existing = _auth_clients_by_loop.get(loop)
    if existing is not None:
        return existing

    lock = _auth_locks_by_loop.get(loop)
    if lock is None:
        lock = asyncio.Lock()
        _auth_locks_by_loop[loop] = lock

    async with lock:
        existing = _auth_clients_by_loop.get(loop)
        if existing is not None:
            return existing
        url, key = require_supabase_auth_config()
        # 타임아웃 설정: Auth 요청을 위한 타임아웃 늘림
        timeout = httpx.Timeout(connect=30.0, read=30.0, write=30.0, pool=60.0)
        options = AsyncClientOptions(
            postgrest_client_timeout=timeout,
            httpx_client=httpx.AsyncClient(timeout=timeout)
        )
        client = await acreate_client(url, key, options=options)
        _auth_clients_by_loop[loop] = client
        return client


def _is_unique_violation(err: APIError) -> bool:
    """Best-effort detection for unique/constraint violations."""

    try:
        payload: Any = err.json()
    except Exception:
        return False

    # PostgREST error payload examples vary; handle common cases.
    code = str(payload.get("code", "")).lower()
    message = str(payload.get("message", "")).lower()
    details = str(payload.get("details", "")).lower()

    # Postgres unique violation SQLSTATE 23505 often appears in details.
    if "23505" in details:
        return True
    if code in {"23505", "unique_violation"}:
        return True
    if "duplicate key" in message or "unique" in message:
        return True
    return False


def translate_postgrest_error(err: APIError, *, default_message: str) -> ExternalServiceError:
    """Translate PostgREST APIError to a stable CRUD-layer error."""

    if _is_unique_violation(err):
        return ConflictError(default_message)

    # Keep original payload accessible via message when helpful.
    try:
        payload = err.json()
    except Exception:
        payload = {"message": str(err)}
    return ExternalServiceError(f"{default_message}. details={payload!r}")


def ensure_single_row(data: Any, *, not_found_message: str) -> dict[str, Any]:
    """Normalize Supabase responses into a single row dict or raise NotFound/External."""

    # For SingleAPIResponse, data is a dict.
    if isinstance(data, dict):
        return data
    raise ExternalServiceError(f"Unexpected response shape: {type(data)!r}")


def ensure_row_list(data: Any) -> list[dict[str, Any]]:
    """Normalize Supabase responses into a list of row dicts."""

    if data is None:
        return []
    if isinstance(data, list):
        # APIResponse.data is List[JSON]
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        return [data]
    raise ExternalServiceError(f"Unexpected response shape: {type(data)!r}")

