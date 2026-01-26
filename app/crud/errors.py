"""CRUD layer errors.

This module provides small, predictable exception types so that:
- API routes (later) can map errors to HTTP status codes
- tests can assert failure modes without depending on Supabase SDK internals
"""

from __future__ import annotations


class CrudError(Exception):
    """Base class for CRUD-layer errors."""


class CrudConfigError(CrudError):
    """Raised when required configuration is missing/invalid."""


class NotFoundError(CrudError):
    """Raised when a requested record does not exist."""


class ConflictError(CrudError):
    """Raised when an operation violates uniqueness/constraints."""


class ExternalServiceError(CrudError):
    """Raised when Supabase/PostgREST returns an unexpected error."""

