"""Auth Router - 인증 관련 API"""

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import get_current_user
from app.core.auth_errors import AuthErrorCode, AuthServiceError, handle_auth_error
from app.core.config import settings
from app.crud.supabase_client import get_supabase_auth_client
from app.schemas.common import ApiResponse
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    SignupRequest,
    TokenRefreshResponse,
)
from app.schemas.user import UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Refresh 토큰을 HttpOnly 쿠키로 설정."""
    response.set_cookie(
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.AUTH_REFRESH_COOKIE_SECURE,
        samesite=settings.AUTH_REFRESH_COOKIE_SAMESITE,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        domain=settings.AUTH_REFRESH_COOKIE_DOMAIN,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Refresh 토큰 쿠키 삭제."""
    response.delete_cookie(
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        domain=settings.AUTH_REFRESH_COOKIE_DOMAIN,
    )


@router.post("/signup", response_model=ApiResponse[AuthResponse], status_code=status.HTTP_201_CREATED)
async def signup(data: SignupRequest, response: Response) -> ApiResponse[AuthResponse]:
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
                    expires_in=0,
                )
            )

        refresh_token = session_data.get("refresh_token")
        if not refresh_token:
            raise AuthServiceError(AuthErrorCode.REFRESH_FAILED, "토큰 갱신에 실패했습니다.")
        _set_refresh_cookie(response, refresh_token)

        return ApiResponse.ok(
            AuthResponse(
                user=user_response,
                access_token=session_data["access_token"],
                expires_in=session_data.get("expires_in", 3600),
            )
        )

    except AuthServiceError as e:
        raise handle_auth_error(e)


@router.post("/login", response_model=ApiResponse[AuthResponse])
async def login(data: LoginRequest, response: Response) -> ApiResponse[AuthResponse]:
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

        refresh_token = session_data.get("refresh_token")
        if not refresh_token:
            raise AuthServiceError(AuthErrorCode.REFRESH_FAILED, "토큰 갱신에 실패했습니다.")
        _set_refresh_cookie(response, refresh_token)

        return ApiResponse.ok(
            AuthResponse(
                user=user_response,
                access_token=session_data["access_token"],
                expires_in=session_data.get("expires_in", 3600),
            )
        )

    except AuthServiceError as e:
        raise handle_auth_error(e)


@router.post("/logout", response_model=ApiResponse[MessageResponse])
async def logout(
    response: Response,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[MessageResponse]:
    """로그아웃

    현재 세션을 종료합니다.
    
    Args:
        current_user: 현재 인증된 사용자 (의존성 주입)
    
    참고:
    - 서버는 refresh token 쿠키를 삭제합니다.
    - access token 폐기는 클라이언트 메모리에서 삭제하여 처리합니다.
    """
    # 현재 사용자가 인증되어 있다는 것을 확인했으므로 성공 응답 반환
    _clear_refresh_cookie(response)
    return ApiResponse.ok(MessageResponse(message="로그아웃 되었습니다."))


@router.post("/refresh", response_model=ApiResponse[TokenRefreshResponse])
async def refresh_token(request: Request, response: Response) -> ApiResponse[TokenRefreshResponse]:
    """토큰 갱신

    HttpOnly 쿠키의 refresh_token으로 새로운 access_token을 발급합니다.
    """
    try:
        refresh_token = request.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
        if not refresh_token:
            raise AuthServiceError(AuthErrorCode.INVALID_TOKEN, "유효하지 않은 토큰입니다.")

        client = await get_supabase_auth_client()

        # Supabase의 refresh_session을 사용하여 새 세션 발급
        refresh_response = await client.auth.refresh_session(refresh_token)

        if refresh_response.session is None:
            raise AuthServiceError(AuthErrorCode.INVALID_TOKEN, "유효하지 않은 토큰입니다.")

        session = refresh_response.session
        access_token = session.access_token if hasattr(session, "access_token") else None
        next_refresh_token = session.refresh_token if hasattr(session, "refresh_token") else None
        expires_in = session.expires_in if hasattr(session, "expires_in") else 3600

        if not access_token or not next_refresh_token:
            raise AuthServiceError(AuthErrorCode.REFRESH_FAILED, "토큰 갱신에 실패했습니다.")

        _set_refresh_cookie(response, next_refresh_token)

        return ApiResponse.ok(
            TokenRefreshResponse(
                access_token=access_token,
                expires_in=expires_in,
            )
        )

    except AuthServiceError as e:
        raise handle_auth_error(e)
    except Exception:
        # 기타 예외는 INVALID_TOKEN으로 처리
        raise handle_auth_error(
            AuthServiceError(AuthErrorCode.INVALID_TOKEN, "유효하지 않은 토큰입니다.")
        )
