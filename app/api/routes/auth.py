"""Auth Router - 인증 관련 API"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.deps import get_current_user, security
from app.core.auth_errors import AuthErrorCode, AuthServiceError, handle_auth_error
from app.crud.supabase_client import get_supabase_auth_client
from app.schemas.common import ApiResponse
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    SignupRequest,
    TokenRefreshResponse,
)
from app.schemas.user import UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=ApiResponse[AuthResponse], status_code=status.HTTP_201_CREATED)
async def signup(data: SignupRequest) -> ApiResponse[AuthResponse]:
    """회원가입

    Supabase Auth를 사용하여 이메일과 비밀번호로 회원가입합니다.
    """
    try:
        user_data, session_data = await auth_service.signup_with_email(
            email=data.email,
            password=data.password,
            name=data.name,
        )

        # Supabase Auth user를 UserResponse로 변환
        user_response = auth_service.supabase_user_to_user_response(user_data["user"])

        # Session이 없으면 이메일 확인이 필요한 경우
        if not session_data.get("access_token"):
            # 이메일 확인이 필요한 경우에도 사용자 정보는 반환
            return ApiResponse.ok(
                AuthResponse(
                    user=user_response,
                    access_token="",  # 이메일 확인 전에는 토큰 없음
                    refresh_token="",
                    expires_in=0,
                ),
                message="회원가입이 완료되었습니다. 이메일을 확인해주세요.",
            )

        return ApiResponse.ok(
            AuthResponse(
                user=user_response,
                access_token=session_data["access_token"],
                refresh_token=session_data["refresh_token"],
                expires_in=session_data.get("expires_in", 3600),
            )
        )

    except AuthServiceError as e:
        raise handle_auth_error(e)


@router.post("/login", response_model=ApiResponse[AuthResponse])
async def login(data: LoginRequest) -> ApiResponse[AuthResponse]:
    """로그인

    Supabase Auth를 사용하여 이메일과 비밀번호로 로그인합니다.
    """
    try:
        user_data, session_data = await auth_service.login_with_email(
            email=data.email,
            password=data.password,
        )

        # Supabase Auth user를 UserResponse로 변환
        user_response = auth_service.supabase_user_to_user_response(user_data["user"])

        return ApiResponse.ok(
            AuthResponse(
                user=user_response,
                access_token=session_data["access_token"],
                refresh_token=session_data["refresh_token"],
                expires_in=session_data.get("expires_in", 3600),
            )
        )

    except AuthServiceError as e:
        raise handle_auth_error(e)


@router.post("/logout", response_model=ApiResponse[MessageResponse])
async def logout(
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[MessageResponse]:
    """로그아웃

    현재 세션을 종료합니다.
    
    Args:
        current_user: 현재 인증된 사용자 (의존성 주입)
    
    참고:
    - Supabase Auth는 클라이언트 사이드에서 세션을 관리합니다.
    - 서버 사이드에서는 사용자 인증 상태를 확인하고 성공 응답을 반환합니다.
    - 실제 세션 종료는 클라이언트에서 access_token과 refresh_token을 삭제하여 처리해야 합니다.
    - 향후 Supabase Admin API를 사용하여 사용자의 모든 세션을 무효화하는 기능 추가 가능.
    """
    # 현재 사용자가 인증되어 있다는 것을 확인했으므로 성공 응답 반환
    # 실제 세션 종료는 클라이언트에서 처리:
    # 1. 클라이언트에서 access_token과 refresh_token을 로컬 스토리지/쿠키에서 삭제
    # 2. 향후 Supabase Admin API를 사용하여 사용자의 모든 세션을 무효화하는 기능 추가 가능
    
    return ApiResponse.ok(MessageResponse(message="로그아웃 되었습니다."))


@router.post("/refresh", response_model=ApiResponse[TokenRefreshResponse])
async def refresh_token(data: RefreshTokenRequest) -> ApiResponse[TokenRefreshResponse]:
    """토큰 갱신

    Supabase Auth의 refresh_token을 사용하여 새로운 access_token을 발급합니다.
    """
    try:
        client = await get_supabase_auth_client()
        
        # Supabase의 refresh_session을 사용하여 새 세션 발급
        response = await client.auth.refresh_session(data.refresh_token)
        
        if response.session is None:
            raise AuthServiceError(AuthErrorCode.INVALID_TOKEN, "유효하지 않은 토큰입니다.")
        
        session = response.session
        access_token = session.access_token if hasattr(session, "access_token") else None
        expires_in = session.expires_in if hasattr(session, "expires_in") else 3600
        
        if not access_token:
            raise AuthServiceError(AuthErrorCode.REFRESH_FAILED, "토큰 갱신에 실패했습니다.")
        
        return ApiResponse.ok(
            TokenRefreshResponse(
                access_token=access_token,
                expires_in=expires_in,
            )
        )
    
    except AuthServiceError as e:
        raise handle_auth_error(e)
    except Exception as e:
        # 기타 예외는 INVALID_TOKEN으로 처리
        raise handle_auth_error(
            AuthServiceError(AuthErrorCode.INVALID_TOKEN, "유효하지 않은 토큰입니다.")
        )

