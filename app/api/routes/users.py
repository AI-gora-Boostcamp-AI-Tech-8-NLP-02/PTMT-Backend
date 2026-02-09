"""Users Router - 사용자 관련 API"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app import crud
from app.crud.errors import CrudConfigError
from app.schemas.common import ApiResponse
from app.schemas.user import UserResponse, UserStats, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_profile(
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[UserResponse]:
    """내 프로필 조회

    현재 로그인한 사용자의 정보와 통계를 조회합니다.
    - total_curriculums: 생성한 커리큘럼 수
    - completed_curriculums: 완료한 커리큘럼 수 (status='ready')
    - total_study_hours: 모든 커리큘럼의 예상 학습 시간 합계
    """
    try:
        # 사용자의 모든 커리큘럼 조회
        curriculums, total_count = await crud.curriculums.get_curriculums_by_user(
            user_id=current_user.id,
            page=1,
            limit=1000,  # 모든 커리큘럼 조회를 위해 큰 값 설정
        )
        
        # 통계 계산
        total_curriculums = total_count
        completed_curriculums = sum(
            1 for c in curriculums 
            if c.get("status") == "ready"
        )
        total_study_hours = sum(
            float(c.get("estimated_hours", 0) or 0) 
            for c in curriculums
        )
        
        # 통계 정보 업데이트
        user_with_stats = UserResponse(
            id=current_user.id,
            email=current_user.email,
            name=current_user.name,
            role=current_user.role,
            avatar_url=current_user.avatar_url,
            created_at=current_user.created_at,
            stats=UserStats(
                total_curriculums=total_curriculums,
                completed_curriculums=completed_curriculums,
                total_study_hours=round(total_study_hours, 1),
            ),
        )
        
        return ApiResponse.ok(user_with_stats)
        
    except CrudConfigError as e:
        # DB 설정이 없는 경우 에러 반환
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "DB 설정이 필요합니다. (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": f"서버 오류가 발생했습니다: {str(e)}",
            },
        )


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
