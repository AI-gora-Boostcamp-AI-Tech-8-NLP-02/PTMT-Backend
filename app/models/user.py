"""User Model - 사용자 테이블 정의

TODO: Supabase PostgreSQL 테이블과 연동
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """사용자 모델
    
    TODO: 실제 DB 연결 시 구현
    - Supabase Auth와 연동 검토
    - 비밀번호 해시 저장
    - 이메일 인증 플래그 추가
    """
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    name: str = Field(max_length=100)
    avatar_url: Optional[str] = Field(default=None)
    role: str = Field(default="user", max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RefreshToken(SQLModel, table=True):
    """리프레시 토큰 모델
    
    TODO: 토큰 관리 구현
    - 만료 체크
    - 로그아웃 시 revoke
    """
    __tablename__ = "refresh_tokens"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(max_length=255, index=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = Field(default=None)
