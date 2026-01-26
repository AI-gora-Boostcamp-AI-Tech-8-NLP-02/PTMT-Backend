"""Auth API Tests

TODO: 실제 인증 로직 구현 후 테스트 보완
"""

from fastapi.testclient import TestClient


def test_signup(client: TestClient):
    """회원가입 테스트"""
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
    assert "refresh_token" in data["data"]


def test_login(client: TestClient):
    """로그인 테스트"""
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


def test_logout(client: TestClient, auth_headers: dict):
    """로그아웃 테스트"""
    response = client.post("/api/auth/logout", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
