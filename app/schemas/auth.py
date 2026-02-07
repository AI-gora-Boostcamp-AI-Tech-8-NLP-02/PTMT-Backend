"""Auth Schemas - 인증 관련 요청/응답 스키마"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str = Field(..., min_length=1)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "password123"
            }
        }
    )


class SignupRequest(BaseModel):
    """회원가입 요청"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="최소 8자 이상")
    name: str = Field(..., min_length=1, max_length=100)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "password123",
                "name": "string"
            }
        }
    )


class AuthResponse(BaseModel):
    """인증 응답 (로그인/회원가입 성공 시)"""
    user: UserResponse
    access_token: str
    expires_in: int = 3600  # 초 단위


class TokenRefreshResponse(BaseModel):
    """토큰 갱신 응답"""
    access_token: str
    expires_in: int = 3600


class MessageResponse(BaseModel):
    """단순 메시지 응답"""
    message: str
