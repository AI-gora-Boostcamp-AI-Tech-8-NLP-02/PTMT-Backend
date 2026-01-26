"""Security Utilities - JWT 토큰 및 비밀번호 처리"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """평문 비밀번호와 해시된 비밀번호 비교
    
    TODO: 실제 인증 시스템에서 사용
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱
    
    TODO: 회원가입 시 비밀번호 저장용
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str | Any,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Access Token 생성
    
    TODO: 로그인 성공 시 호출
    
    Args:
        subject: 토큰에 포함될 사용자 식별자 (보통 user_id)
        expires_delta: 만료 시간 (기본값: 설정에서 가져옴)
    
    Returns:
        JWT 토큰 문자열
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(
    subject: str | Any,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Refresh Token 생성
    
    TODO: 로그인 성공 시 Access Token과 함께 발급
    
    Args:
        subject: 토큰에 포함될 사용자 식별자
        expires_delta: 만료 시간 (기본값: 7일)
    
    Returns:
        JWT 토큰 문자열
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """토큰 검증 및 subject 추출
    
    TODO: 인증이 필요한 API에서 사용
    
    Args:
        token: JWT 토큰 문자열
        token_type: 토큰 타입 ("access" or "refresh")
    
    Returns:
        토큰이 유효하면 subject (user_id), 아니면 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        
        # 토큰 타입 확인
        if payload.get("type") != token_type:
            return None
        
        subject: str = payload.get("sub")
        if subject is None:
            return None
        
        return subject
    except JWTError:
        return None
