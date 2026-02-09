"""CRUD layer (Supabase/PostgREST).

This package provides database access primitives used by API routes/services.
"""

from . import curriculums, junctions, papers, refresh_tokens, users
from .errors import (
    ConflictError,
    CrudConfigError,
    CrudError,
    ExternalServiceError,
    NotFoundError,
)
from .supabase_client import get_supabase_client, require_supabase_config
