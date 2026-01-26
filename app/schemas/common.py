"""Common Schemas - 공통 응답 형식 정의"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """에러 상세 정보"""
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class ApiResponse(BaseModel, Generic[T]):
    """API 표준 응답 형식
    
    모든 API는 이 형식으로 응답합니다:
    - 성공: {"success": true, "data": {...}}
    - 실패: {"success": false, "error": {...}}
    """
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None

    @classmethod
    def ok(cls, data: T) -> "ApiResponse[T]":
        """성공 응답 생성 헬퍼"""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, code: str, message: str, details: Optional[dict] = None) -> "ApiResponse":
        """실패 응답 생성 헬퍼"""
        return cls(
            success=False,
            error=ErrorDetail(code=code, message=message, details=details)
        )


class PaginationInfo(BaseModel):
    """페이지네이션 정보"""
    page: int
    limit: int
    total: int
    has_more: bool
