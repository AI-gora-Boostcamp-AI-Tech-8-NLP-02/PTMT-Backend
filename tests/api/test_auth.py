"""Auth API Tests."""

from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.core.config import settings
from app.main import app
from app.schemas.user import UserResponse, UserStats


def _fake_user_payload(email: str = "test@example.com", name: str = "테스트 사용자") -> dict:
    return {
        "id": "a02f767f-e32e-4c4b-9ec4-8ce20cd1475e",
        "email": email,
        "name": name,
        "user_metadata": {"name": name},
        "created_at": "2026-01-01T00:00:00Z",
    }


def _fake_user_response(email: str = "test@example.com", name: str = "테스트 사용자") -> UserResponse:
    return UserResponse(
        id="a02f767f-e32e-4c4b-9ec4-8ce20cd1475e",
        email=email,
        name=name,
        role="user",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        stats=UserStats(total_curriculums=0, completed_curriculums=0, total_study_hours=0.0),
    )


def test_signup_sets_refresh_cookie_and_hides_refresh_token(client: TestClient, monkeypatch):
    """회원가입 성공 시 refresh token은 쿠키로만 내려가야 한다."""

    async def fake_signup_with_email(*, email: str, password: str, name: str):
        return (
            {"user": _fake_user_payload(email=email, name=name)},
            {
                "access_token": "access-from-signup",
                "refresh_token": "refresh-from-signup",
                "expires_in": 3600,
            },
        )

    monkeypatch.setattr(
        "app.api.routes.auth.auth_service.signup_with_email",
        fake_signup_with_email,
    )
    monkeypatch.setattr(
        "app.api.routes.auth.auth_service.supabase_user_to_user_response",
        lambda user: _fake_user_response(email=user["email"], name=user["name"]),
    )

    response = client.post(
        "/api/auth/signup",
        json={
            "email": "test@example.com",
            "password": "password123",
            "name": "테스트 사용자",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" not in data["data"]

    set_cookie = response.headers.get("set-cookie", "")
    assert settings.AUTH_REFRESH_COOKIE_NAME in set_cookie
    assert "HttpOnly" in set_cookie


def test_login_sets_refresh_cookie_and_hides_refresh_token(client: TestClient, monkeypatch):
    """로그인 성공 시 refresh token은 쿠키로만 내려가야 한다."""

    async def fake_login_with_email(*, email: str, password: str):
        return (
            {"user": _fake_user_payload(email=email, name="로그인 사용자")},
            {
                "access_token": "access-from-login",
                "refresh_token": "refresh-from-login",
                "expires_in": 3600,
            },
        )

    monkeypatch.setattr(
        "app.api.routes.auth.auth_service.login_with_email",
        fake_login_with_email,
    )
    monkeypatch.setattr(
        "app.api.routes.auth.auth_service.supabase_user_to_user_response",
        lambda user: _fake_user_response(email=user["email"], name=user["name"]),
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "demo@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" not in data["data"]

    set_cookie = response.headers.get("set-cookie", "")
    assert settings.AUTH_REFRESH_COOKIE_NAME in set_cookie
    assert "HttpOnly" in set_cookie


def test_refresh_uses_cookie_and_rotates_cookie(client: TestClient, monkeypatch):
    """refresh는 body가 아닌 쿠키를 읽고 refresh 쿠키를 재설정해야 한다."""

    class _DummyAuth:
        async def refresh_session(self, refresh_token: str):
            assert refresh_token == "old-refresh-token"
            return SimpleNamespace(
                session=SimpleNamespace(
                    access_token="new-access-token",
                    refresh_token="new-refresh-token",
                    expires_in=3600,
                )
            )

    class _DummyClient:
        auth = _DummyAuth()

    async def fake_get_supabase_auth_client():
        return _DummyClient()

    monkeypatch.setattr(
        "app.api.routes.auth.get_supabase_auth_client",
        fake_get_supabase_auth_client,
    )

    response = client.post(
        "/api/auth/refresh",
        cookies={settings.AUTH_REFRESH_COOKIE_NAME: "old-refresh-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["access_token"] == "new-access-token"

    set_cookie = response.headers.get("set-cookie", "")
    assert settings.AUTH_REFRESH_COOKIE_NAME in set_cookie
    assert "new-refresh-token" in set_cookie


def test_refresh_without_cookie_returns_401(client: TestClient):
    """refresh 쿠키가 없으면 INVALID_TOKEN(401)을 반환해야 한다."""
    response = client.post("/api/auth/refresh")

    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["code"] == "INVALID_TOKEN"


def test_logout_clears_refresh_cookie(client: TestClient):
    """로그아웃 시 refresh 쿠키가 삭제되어야 한다."""

    async def override_current_user() -> UserResponse:
        return _fake_user_response()

    app.dependency_overrides[get_current_user] = override_current_user
    try:
        response = client.post(
            "/api/auth/logout",
            cookies={settings.AUTH_REFRESH_COOKIE_NAME: "to-delete"},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    set_cookie = response.headers.get("set-cookie", "")
    assert settings.AUTH_REFRESH_COOKIE_NAME in set_cookie
    assert "Max-Age=0" in set_cookie or "expires=" in set_cookie.lower()
