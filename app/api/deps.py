"""API Dependencies - 의존성 주입"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.crud.supabase_client import get_supabase_auth_client
from app.schemas.user import UserResponse
from app.services import auth_service

# Bearer 토큰 스키마
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> UserResponse:
    """현재 인증된 사용자 반환

    Supabase Auth JWT 토큰을 검증하여 사용자 정보를 반환합니다.
    """
    # 개발 모드에서는 토큰 없이도 더미 사용자 반환 (옵션)
    if settings.DEBUG and credentials is None:
        # 개발 모드: 토큰 없어도 더미 사용자 반환 (필요시 주석 처리)
        # return DUMMY_USER
        pass

    # 토큰이 없으면 에러
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Supabase Auth를 사용하여 토큰 검증 및 사용자 정보 조회
        client = await get_supabase_auth_client()
        response = await client.auth.get_user(token)

        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Supabase Auth user를 UserResponse로 변환
        user_dict = response.user.model_dump() if hasattr(response.user, "model_dump") else dict(response.user) if hasattr(response.user, "__dict__") else {}
        user_response = auth_service.supabase_user_to_user_response(user_dict)

        return user_response

    except Exception as e:
        # Supabase Auth 에러 또는 기타 예외 처리
        error_str = str(e).lower()
        # Auth 관련 에러인지 확인
        if "auth" in error_str or "token" in error_str or "unauthorized" in error_str or "invalid" in error_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 중 오류가 발생했습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[UserResponse]:
    """선택적 인증 - 인증 없어도 접근 가능하지만, 있으면 사용자 정보 제공

    TODO: 공개 API에서 사용
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

