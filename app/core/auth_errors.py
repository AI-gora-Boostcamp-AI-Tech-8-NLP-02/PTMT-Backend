"""Auth Error Handling - 인증 관련 에러 처리 유틸리티"""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.config import settings


class AuthErrorCode:
    """Auth 에러 코드 상수"""

    # 설정 오류
    CONFIG_ERROR = "CONFIG_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"

    # 인증 오류
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    EMAIL_NOT_CONFIRMED = "EMAIL_NOT_CONFIRMED"

    # 회원가입 오류
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    SIGNUP_FAILED = "SIGNUP_FAILED"

    # 로그인 오류
    LOGIN_FAILED = "LOGIN_FAILED"

    # 토큰 오류
    INVALID_TOKEN = "INVALID_TOKEN"
    REFRESH_FAILED = "REFRESH_FAILED"


class AuthServiceError(Exception):
    """Auth 서비스 에러"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def extract_error_message(e: Exception) -> str:
    """예외 객체에서 에러 메시지 추출

    Args:
        e: 예외 객체

    Returns:
        에러 메시지 문자열
    """
    error_message = str(e)
    if hasattr(e, "message"):
        error_message = str(e.message)
    elif hasattr(e, "msg"):
        error_message = str(e.msg)
    elif hasattr(e, "error"):
        error_message = str(e.error)
    return error_message


def validate_supabase_config() -> None:
    """Supabase 설정 값 검증

    Raises:
        AuthServiceError: 설정이 잘못된 경우
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_URL.strip():
        raise AuthServiceError(
            AuthErrorCode.CONFIG_ERROR,
            "SUPABASE_URL이 설정되지 않았습니다. .env 파일에 SUPABASE_URL을 설정해주세요.",
        )

    if not settings.SUPABASE_ANON_KEY or not settings.SUPABASE_ANON_KEY.strip():
        raise AuthServiceError(
            AuthErrorCode.CONFIG_ERROR,
            "SUPABASE_ANON_KEY가 설정되지 않았습니다. .env 파일에 SUPABASE_ANON_KEY를 설정해주세요.",
        )

    # URL 형식 검증
    url = settings.SUPABASE_URL.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        raise AuthServiceError(
            AuthErrorCode.CONFIG_ERROR,
            f"SUPABASE_URL 형식이 잘못되었습니다. https://로 시작해야 합니다. 현재 값: {url[:50]}...",
        )


def classify_auth_error(e: Exception, operation: str = "AUTH") -> tuple[str, str]:
    """예외를 Auth 에러 코드와 메시지로 분류

    Args:
        e: 예외 객체
        operation: 작업 유형 ("SIGNUP", "LOGIN", "AUTH")

    Returns:
        (error_code, error_message) 튜플
    """
    error_type = type(e).__name__
    error_type_lower = error_type.lower()
    error_message = extract_error_message(e)
    error_message_lower = error_message.lower() if error_message else ""

    # 네트워크 연결 오류 처리
    if (
        "connecttimeout" in error_type_lower
        or "timeout" in error_type_lower
        or "connection" in error_message_lower
        or "network" in error_message_lower
        or "unreachable" in error_message_lower
        or "resolve" in error_message_lower
        or "dns" in error_message_lower
    ):
        url_info = (
            f"URL: {settings.SUPABASE_URL[:50]}..."
            if settings.SUPABASE_URL
            else "URL: (설정되지 않음)"
        )
        key_info = (
            f"ANON_KEY: {'설정됨' if settings.SUPABASE_ANON_KEY else '설정되지 않음'}"
        )

        return (
            AuthErrorCode.CONNECTION_ERROR,
            f"Supabase 서버에 연결할 수 없습니다. ({error_type}: {error_message[:100]}) "
            f"{url_info}, {key_info}. 네트워크 연결과 설정을 확인해주세요.",
        )

    # 이메일 중복 체크 (회원가입 시)
    if operation == "SIGNUP" and (
        "already registered" in error_message_lower
        or "user already" in error_message_lower
        or ("email" in error_message_lower and "exists" in error_message_lower)
        or "duplicate" in error_message_lower
    ):
        return (
            AuthErrorCode.EMAIL_ALREADY_EXISTS,
            "이미 사용 중인 이메일입니다.",
        )

    # 잘못된 자격증명 체크 (로그인 시)
    if operation == "LOGIN" and (
        "invalid" in error_message_lower
        or "credentials" in error_message_lower
        or "password" in error_message_lower
        or ("email" in error_message_lower and "password" in error_message_lower)
        or "wrong" in error_message_lower
    ):
        return (
            AuthErrorCode.INVALID_CREDENTIALS,
            "이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    # 이메일 미인증 체크
    if (
        "email not confirmed" in error_message_lower
        or "not confirmed" in error_message_lower
        or "email confirmation" in error_message_lower
    ):
        return (
            AuthErrorCode.EMAIL_NOT_CONFIRMED,
            "이메일 인증이 필요합니다.",
        )

    # AuthError 타입 체크 (gotrue 패키지가 있는 경우)
    if "auth" in error_type_lower or "autherror" in error_type_lower:
        detail_msg = error_message if error_message else "알 수 없는 오류"
        if operation == "SIGNUP":
            return (
                AuthErrorCode.SIGNUP_FAILED,
                f"회원가입에 실패했습니다: {detail_msg}",
            )
        elif operation == "LOGIN":
            return (
                AuthErrorCode.LOGIN_FAILED,
                f"로그인에 실패했습니다: {detail_msg}",
            )

    # 일반 예외 처리
    detail_msg = error_message if error_message else f"예외 타입: {error_type}"
    if operation == "SIGNUP":
        return (
            AuthErrorCode.SIGNUP_FAILED,
            f"회원가입 중 오류가 발생했습니다: {detail_msg}",
        )
    elif operation == "LOGIN":
        return (
            AuthErrorCode.LOGIN_FAILED,
            f"로그인 중 오류가 발생했습니다: {detail_msg}",
        )
    else:
        return (
            AuthErrorCode.CONNECTION_ERROR,
            f"인증 중 오류가 발생했습니다: {detail_msg}",
        )


def handle_auth_error(e: AuthServiceError) -> HTTPException:
    """AuthServiceError를 HTTPException으로 변환

    Args:
        e: AuthServiceError 객체

    Returns:
        HTTPException 객체
    """
    # 에러 코드에 따라 적절한 HTTP 상태 코드 매핑
    status_code_map = {
        AuthErrorCode.EMAIL_ALREADY_EXISTS: status.HTTP_409_CONFLICT,
        AuthErrorCode.INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
        AuthErrorCode.EMAIL_NOT_CONFIRMED: status.HTTP_403_FORBIDDEN,
        AuthErrorCode.CONNECTION_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
        AuthErrorCode.CONFIG_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
        AuthErrorCode.SIGNUP_FAILED: status.HTTP_400_BAD_REQUEST,
        AuthErrorCode.LOGIN_FAILED: status.HTTP_401_UNAUTHORIZED,
        AuthErrorCode.INVALID_TOKEN: status.HTTP_401_UNAUTHORIZED,
        AuthErrorCode.REFRESH_FAILED: status.HTTP_400_BAD_REQUEST,
    }

    status_code = status_code_map.get(e.code, status.HTTP_400_BAD_REQUEST)

    return HTTPException(
        status_code=status_code,
        detail={
            "code": e.code,
            "message": e.message,
        },
    )
