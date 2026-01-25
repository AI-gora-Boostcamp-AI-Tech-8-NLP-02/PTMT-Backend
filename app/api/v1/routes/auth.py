"""Auth Router - 인증 관련 API

TODO: 실제 구현 시
- Supabase Auth 연동 또는 직접 구현
- 비밀번호 해싱 및 검증
- 토큰 저장 및 관리
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import get_current_user, DUMMY_USER
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_password_hash,
)
from app.schemas.common import ApiResponse
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    SignupRequest,
    TokenRefreshResponse,
)
from app.schemas.user import UserResponse, UserStats

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=ApiResponse[AuthResponse], status_code=status.HTTP_201_CREATED)
async def signup(data: SignupRequest) -> ApiResponse[AuthResponse]:
    """회원가입
    
    TODO: 실제 구현
    1. 이메일 중복 체크
    2. 비밀번호 해싱
    3. 사용자 생성
    4. JWT 토큰 발급
    """
    # TODO: 이메일 중복 체크
    # existing_user = await crud.user.get_by_email(db, email=data.email)
    # if existing_user:
    #     return ApiResponse.fail("EMAIL_ALREADY_EXISTS", "이미 사용 중인 이메일입니다.")
    
    # TODO: 비밀번호 해싱 및 사용자 생성
    # password_hash = get_password_hash(data.password)
    # user = await crud.user.create(db, email=data.email, password_hash=password_hash, name=data.name)
    
    # 더미 사용자 생성
    dummy_user = UserResponse(
        id="user-new-" + str(hash(data.email))[-6:],
        email=data.email,
        name=data.name,
        role="user",
        avatar_url=None,
        created_at=datetime.utcnow(),
        stats=UserStats(
            total_curriculums=0,
            completed_curriculums=0,
            total_study_hours=0.0,
        ),
    )
    
    # 토큰 생성
    access_token = create_access_token(subject=dummy_user.id)
    refresh_token = create_refresh_token(subject=dummy_user.id)
    
    # TODO: refresh_token을 DB에 저장
    # await crud.refresh_token.create(db, user_id=user.id, token_hash=hash(refresh_token))
    
    return ApiResponse.ok(
        AuthResponse(
            user=dummy_user,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,
        )
    )


@router.post("/login", response_model=ApiResponse[AuthResponse])
async def login(data: LoginRequest) -> ApiResponse[AuthResponse]:
    """로그인
    
    TODO: 실제 구현
    1. 이메일로 사용자 조회
    2. 비밀번호 검증
    3. JWT 토큰 발급
    """
    # TODO: 사용자 조회
    # user = await crud.user.get_by_email(db, email=data.email)
    # if not user:
    #     return ApiResponse.fail("INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않습니다.")
    
    # TODO: 비밀번호 검증
    # if not verify_password(data.password, user.password_hash):
    #     return ApiResponse.fail("INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않습니다.")
    
    # 더미 응답: 모든 로그인 성공
    dummy_user = UserResponse(
        id="user-dummy-123",
        email=data.email,
        name="홍길동",
        role="user",
        avatar_url=None,
        created_at=datetime.utcnow(),
        stats=UserStats(
            total_curriculums=5,
            completed_curriculums=3,
            total_study_hours=24.5,
        ),
    )
    
    # 토큰 생성
    access_token = create_access_token(subject=dummy_user.id)
    refresh_token = create_refresh_token(subject=dummy_user.id)
    
    return ApiResponse.ok(
        AuthResponse(
            user=dummy_user,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,
        )
    )


@router.post("/logout", response_model=ApiResponse[MessageResponse])
async def logout(
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[MessageResponse]:
    """로그아웃
    
    TODO: 실제 구현
    1. refresh_token 무효화
    2. 필요시 access_token 블랙리스트 추가
    """
    # TODO: refresh_token 무효화
    # await crud.refresh_token.revoke_all(db, user_id=current_user.id)
    
    return ApiResponse.ok(
        MessageResponse(message="로그아웃 되었습니다.")
    )


@router.post("/refresh", response_model=ApiResponse[TokenRefreshResponse])
async def refresh_token(data: RefreshTokenRequest) -> ApiResponse[TokenRefreshResponse]:
    """토큰 갱신
    
    TODO: 실제 구현
    1. refresh_token 검증
    2. DB에서 토큰 유효성 확인
    3. 새 access_token 발급
    """
    # TODO: refresh_token 검증
    user_id = verify_token(data.refresh_token, token_type="refresh")
    
    # 더미 모드: 모든 refresh_token 허용
    if user_id is None:
        # TODO: 실제 구현 시 에러 반환
        # return ApiResponse.fail("INVALID_TOKEN", "유효하지 않은 토큰입니다.")
        user_id = "user-dummy-123"  # 더미 사용자
    
    # TODO: DB에서 토큰 유효성 확인
    # token_record = await crud.refresh_token.get_by_hash(db, token_hash=hash(data.refresh_token))
    # if not token_record or token_record.revoked_at:
    #     return ApiResponse.fail("INVALID_TOKEN", "토큰이 만료되었거나 취소되었습니다.")
    
    # 새 access_token 발급
    new_access_token = create_access_token(subject=user_id)
    
    return ApiResponse.ok(
        TokenRefreshResponse(
            access_token=new_access_token,
            expires_in=3600,
        )
    )
