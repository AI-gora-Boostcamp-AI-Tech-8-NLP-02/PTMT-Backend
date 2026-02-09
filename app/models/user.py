"""User Model - 사용자 테이블 정의

TODO: Supabase PostgreSQL 테이블과 연동
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """사용자 모델
    
    Supabase Auth와 연동되는 커스텀 users 테이블
    - 비밀번호는 Supabase Auth에서 관리하므로 password_hash 필드 없음
    - auth.users와 동일한 id 사용
    """
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    name: str = Field(max_length=100)
    avatar_url: Optional[str] = Field(default=None)
    role: str = Field(default="user", max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_insert_dict(self) -> dict:
        """Supabase insert용 딕셔너리 변환"""
        return {
            "id": str(self.id),
            "email": self.email,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class RefreshToken(SQLModel, table=True):
    """리프레시 토큰 모델
    
    Note: Supabase Auth에서 토큰을 관리하므로 이 테이블은 현재 사용되지 않음
    향후 추가 토큰 관리가 필요한 경우 사용
    """
    __tablename__ = "refresh_tokens"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(max_length=255, index=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = Field(default=None)
