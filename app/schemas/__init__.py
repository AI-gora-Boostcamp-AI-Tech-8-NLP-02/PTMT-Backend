"""Pydantic Schemas - API 요청/응답 스키마 정의"""

from app.schemas.common import ApiResponse, ErrorDetail, PaginationInfo
from app.schemas.auth import (
    LoginRequest,
    SignupRequest,
    RefreshTokenRequest,
    AuthResponse,
    TokenRefreshResponse,
    MessageResponse,
)
from app.schemas.user import (
    UserResponse,
    UserUpdateRequest,
    UserStats,
)
from app.schemas.paper import (
    LinkSubmitRequest,
    TitleSearchRequest,
    PaperUploadResponse,
    Keyword,
)
from app.schemas.curriculum import (
    CurriculumOptions,
    CurriculumListItem,
    CurriculumResponse,
    CurriculumListResponse,
    GenerationStartResponse,
    GenerationStatusResponse,
    CurriculumGraphResponse,
    CurriculumImportRequest,
    CurriculumImportFailedRequest,
    CurriculumImportResponse,
)

__all__ = [
    # Common
    "ApiResponse",
    "ErrorDetail",
    "PaginationInfo",
    # Auth
    "LoginRequest",
    "SignupRequest",
    "RefreshTokenRequest",
    "AuthResponse",
    "TokenRefreshResponse",
    "MessageResponse",
    # User
    "UserResponse",
    "UserUpdateRequest",
    "UserStats",
    # Paper
    "LinkSubmitRequest",
    "TitleSearchRequest",
    "PaperUploadResponse",
    "Keyword",
    # Curriculum
    "CurriculumOptions",
    "CurriculumListItem",
    "CurriculumResponse",
    "CurriculumListResponse",
    "GenerationStartResponse",
    "GenerationStatusResponse",
    "CurriculumGraphResponse",
    "CurriculumImportRequest",
    "CurriculumImportFailedRequest",
    "CurriculumImportResponse",
]
