"""User Schemas - 사용자 관련 요청/응답 스키마"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserStats(BaseModel):
    """사용자 통계"""
    total_curriculums: int = 0
    completed_curriculums: int = 0
    total_study_hours: float = 0.0


class UserResponse(BaseModel):
    """사용자 정보 응답"""
    id: str
    email: EmailStr
    name: str
    role: str = "user"
    avatar_url: Optional[str] = None
    created_at: datetime
    stats: Optional[UserStats] = None


class UserUpdateRequest(BaseModel):
    """프로필 수정 요청"""
    name: Optional[str] = None
    avatar_url: Optional[str] = None
