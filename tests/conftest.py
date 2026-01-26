"""Pytest Configuration and Fixtures

TODO: 실제 테스트 환경 구성
- 테스트 DB 설정
- 테스트 클라이언트
- 인증 fixture
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """테스트 클라이언트 fixture"""
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict:
    """인증 헤더 fixture
    
    TODO: 실제 테스트에서는 로그인 후 토큰 사용
    """
    return {"Authorization": "Bearer dummy-test-token"}


# TODO: 테스트 DB fixture
# @pytest.fixture
# async def db_session():
#     async with async_session() as session:
#         yield session
#         await session.rollback()
