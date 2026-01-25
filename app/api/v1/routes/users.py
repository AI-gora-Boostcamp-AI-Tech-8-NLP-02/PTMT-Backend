"""Users Router - 사용자 관련 API

TODO: 실제 구현 시
- DB에서 사용자 정보 조회/수정
- 통계 정보 계산
"""

from datetime import datetime

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_user
from app.schemas.common import ApiResponse
from app.schemas.user import UserResponse, UserStats, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_profile(
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[UserResponse]:
    """내 프로필 조회
    
    TODO: 실제 구현
    1. 현재 사용자 정보 반환 (get_current_user에서 처리됨)
    2. 통계 정보 계산 (total_curriculums, completed 등)
    """
    # TODO: 통계 정보 계산
    # stats = await calculate_user_stats(db, user_id=current_user.id)
    # current_user.stats = stats
    
    return ApiResponse.ok(current_user)


@router.patch("/me", response_model=ApiResponse[UserResponse])
async def update_profile(
    data: UserUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[UserResponse]:
    """프로필 수정
    
    TODO: 실제 구현
    1. 유효성 검사
    2. DB 업데이트
    3. 수정된 사용자 정보 반환
    """
    # TODO: DB 업데이트
    # updated_fields = data.model_dump(exclude_unset=True)
    # updated_user = await crud.user.update(db, id=current_user.id, **updated_fields)
    
    # 더미 응답: 요청된 필드 반영
    updated_user = UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=data.name if data.name else current_user.name,
        role=current_user.role,
        avatar_url=data.avatar_url if data.avatar_url is not None else current_user.avatar_url,
        created_at=current_user.created_at,
        stats=current_user.stats,
    )
    
    return ApiResponse.ok(updated_user)
