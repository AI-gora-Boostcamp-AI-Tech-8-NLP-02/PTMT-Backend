"""API Dependencies - 의존성 주입

TODO: 실제 DB 세션 및 인증 구현
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.security import verify_token
from app.schemas.user import UserResponse, UserStats

# Bearer 토큰 스키마
security = HTTPBearer(auto_error=False)


# ===========================================
# 더미 사용자 데이터
# ===========================================

DUMMY_USER = UserResponse(
    id="user-dummy-123",
    email="demo@example.com",
    name="홍길동",
    role="user",
    avatar_url=None,
    created_at="2024-01-01T00:00:00Z",
    stats=UserStats(
        total_curriculums=5,
        completed_curriculums=3,
        total_study_hours=24.5,
    ),
)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> UserResponse:
    """현재 인증된 사용자 반환

    TODO: 실제 구현 시
    1. 토큰 검증
    2. DB에서 사용자 조회
    3. 사용자 정보 반환

    현재는 더미 사용자 반환
    """
    # 개발 모드에서는 토큰 없이도 더미 사용자 반환
    if settings.DEBUG:
        if credentials is None:
            # 개발 모드: 토큰 없어도 더미 사용자 반환
            return DUMMY_USER

        # 토큰이 있으면 검증 시도 (실패해도 더미 사용자 반환)
        token = credentials.credentials
        user_id = verify_token(token)
        # 검증 결과와 상관없이 더미 사용자 반환
        return DUMMY_USER

    # 프로덕션 모드: 엄격한 인증
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 토큰 검증
    token = credentials.credentials
    user_id = verify_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # TODO: DB에서 사용자 조회
    # user = await crud.user.get(db, id=user_id)
    # if user is None:
    #     raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    return DUMMY_USER


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

