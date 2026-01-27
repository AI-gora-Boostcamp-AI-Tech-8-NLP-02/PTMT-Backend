"""Auth Service - Supabase Auth를 사용한 인증 서비스"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.auth_errors import (
    AuthErrorCode,
    AuthServiceError,
    classify_auth_error,
    validate_supabase_config,
)
from app.crud.supabase_client import get_supabase_auth_client, get_supabase_client
from app.schemas.user import UserResponse, UserStats


async def signup_with_email(
    *, email: str, password: str, name: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """이메일과 비밀번호로 회원가입

    Args:
        email: 사용자 이메일
        password: 비밀번호
        name: 사용자 이름

    Returns:
        (user_data, session_data) 튜플
        - user_data: Supabase Auth user 정보
        - session_data: access_token, refresh_token 등 세션 정보

    Raises:
        AuthServiceError: 회원가입 실패 시 (이메일 중복 등)
    """
    # 설정 검증
    validate_supabase_config()

    try:
        client = await get_supabase_auth_client()
    except Exception as config_error:
        error_msg = str(config_error)
        raise AuthServiceError(
            AuthErrorCode.CONFIG_ERROR,
            f"Supabase 클라이언트 생성 실패: {error_msg}. SUPABASE_URL과 SUPABASE_ANON_KEY를 확인해주세요.",
        )

    try:
        # Supabase Auth signUp 호출 (user_metadata에 name 포함)
        response = await client.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "name": name,
                    }
                }
            }
        )

        # 에러 체크
        if response.user is None:
            raise AuthServiceError(
                AuthErrorCode.SIGNUP_FAILED, "회원가입에 실패했습니다. 다시 시도해주세요."
            )

        user = response.user
        session = response.session

        # Supabase Auth user 정보를 딕셔너리로 변환
        user_dict = user.model_dump() if hasattr(user, "model_dump") else dict(user) if hasattr(user, "__dict__") else {}
        auth_user_id = str(user_dict.get("id", ""))
        
        # 커스텀 users 테이블에 레코드 생성
        # Supabase Auth의 user.id를 그대로 사용
        try:
            # user_metadata에서 name 추출 (없으면 파라미터의 name 사용)
            user_metadata = user_dict.get("user_metadata", {})
            user_name = user_metadata.get("name", name)
            avatar_url = user_metadata.get("avatar_url")
            
            # Supabase 클라이언트를 사용하여 id를 명시적으로 지정하여 insert
            supabase_client = await get_supabase_client()
            payload = {
                "id": auth_user_id,  # Supabase Auth의 user.id 사용
                "email": email,
                "password_hash": "",  # Supabase Auth에서 관리하므로 빈 값
                "name": user_name,
                "avatar_url": avatar_url,
                "role": "user",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            await supabase_client.table("users").insert(payload).execute()
        except Exception as db_error:
            # users 테이블 생성 실패 시 로깅 (선택적)
            # Auth는 성공했으므로 계속 진행하되, 에러 정보는 보관
            error_str = str(db_error).lower()
            # 이미 존재하는 경우는 무시 (중복 생성 방지)
            if "duplicate" not in error_str and "already exists" not in error_str and "unique" not in error_str:
                # 다른 에러는 로깅하거나 처리
                pass

        # Session이 없으면 이메일 확인이 필요한 경우
        if session is None:
            return {"user": user_dict, "session": None}, {}

        # Session이 있는 경우
        session_dict = session.model_dump() if hasattr(session, "model_dump") else dict(session) if hasattr(session, "__dict__") else {}
        
        return {"user": user_dict, "session": session_dict}, {
            "access_token": session.access_token if hasattr(session, "access_token") else session_dict.get("access_token"),
            "refresh_token": session.refresh_token if hasattr(session, "refresh_token") else session_dict.get("refresh_token"),
            "expires_in": session.expires_in if hasattr(session, "expires_in") else session_dict.get("expires_in"),
        }

    except AuthServiceError:
        # 이미 AuthServiceError인 경우 그대로 재발생
        raise
    except Exception as e:
        # 예외를 Auth 에러로 분류
        error_code, error_message = classify_auth_error(e, operation="SIGNUP")
        raise AuthServiceError(error_code, error_message)


async def login_with_email(*, email: str, password: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """이메일과 비밀번호로 로그인

    Args:
        email: 사용자 이메일
        password: 비밀번호

    Returns:
        (user_data, session_data) 튜플
        - user_data: Supabase Auth user 정보
        - session_data: access_token, refresh_token 등 세션 정보

    Raises:
        AuthServiceError: 로그인 실패 시 (잘못된 자격증명 등)
    """
    # 설정 검증
    validate_supabase_config()

    try:
        client = await get_supabase_auth_client()
    except Exception as config_error:
        error_msg = str(config_error)
        raise AuthServiceError(
            AuthErrorCode.CONFIG_ERROR,
            f"Supabase 클라이언트 생성 실패: {error_msg}. SUPABASE_URL과 SUPABASE_ANON_KEY를 확인해주세요.",
        )

    try:
        # Supabase Auth signInWithPassword 호출
        response = await client.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )

        if response.user is None or response.session is None:
            raise AuthServiceError(
                AuthErrorCode.INVALID_CREDENTIALS, "이메일 또는 비밀번호가 올바르지 않습니다."
            )

        user = response.user
        session = response.session

        user_dict = user.model_dump() if hasattr(user, "model_dump") else dict(user) if hasattr(user, "__dict__") else {}
        session_dict = session.model_dump() if hasattr(session, "model_dump") else dict(session) if hasattr(session, "__dict__") else {}

        return {"user": user_dict, "session": session_dict}, {
            "access_token": session.access_token if hasattr(session, "access_token") else session_dict.get("access_token"),
            "refresh_token": session.refresh_token if hasattr(session, "refresh_token") else session_dict.get("refresh_token"),
            "expires_in": session.expires_in if hasattr(session, "expires_in") else session_dict.get("expires_in"),
        }

    except AuthServiceError:
        # 이미 AuthServiceError인 경우 그대로 재발생
        raise
    except Exception as e:
        # 예외를 Auth 에러로 분류
        error_code, error_message = classify_auth_error(e, operation="LOGIN")
        raise AuthServiceError(error_code, error_message)


def supabase_user_to_user_response(user_data: dict[str, Any]) -> UserResponse:
    """Supabase Auth user 데이터를 UserResponse로 변환

    Args:
        user_data: Supabase Auth user 딕셔너리

    Returns:
        UserResponse 객체
    """
    user_id = str(user_data.get("id", ""))
    email = user_data.get("email", "")
    user_metadata = user_data.get("user_metadata", {})
    name = user_metadata.get("name", email.split("@")[0] if email else "User")
    avatar_url = user_metadata.get("avatar_url")
    created_at_str = user_data.get("created_at")
    
    # created_at 파싱
    if created_at_str:
        try:
            # Supabase는 ISO 형식 문자열을 반환
            if isinstance(created_at_str, str):
                # ISO 형식 문자열 처리 (Z 또는 +00:00)
                if created_at_str.endswith("Z"):
                    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                elif "+" in created_at_str or created_at_str.count("-") >= 3:
                    created_at = datetime.fromisoformat(created_at_str)
                else:
                    # 타임스탬프인 경우
                    created_at = datetime.fromtimestamp(float(created_at_str), tz=timezone.utc)
            else:
                created_at = datetime.fromtimestamp(created_at_str, tz=timezone.utc)
        except Exception:
            created_at = datetime.now(timezone.utc)
    else:
        created_at = datetime.now(timezone.utc)

    return UserResponse(
        id=user_id,
        email=email,
        name=name,
        role="user",  # 기본값, 필요시 user_metadata에서 가져올 수 있음
        avatar_url=avatar_url,
        created_at=created_at,
        stats=UserStats(
            total_curriculums=0,
            completed_curriculums=0,
            total_study_hours=0.0,
        ),
    )
