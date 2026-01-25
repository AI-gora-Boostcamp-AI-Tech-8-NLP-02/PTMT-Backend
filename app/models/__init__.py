"""SQLModel Models - 데이터베이스 모델 정의

테이블 구조:
- users: 사용자 정보
- refresh_tokens: JWT 리프레시 토큰 관리
- papers: 업로드된 논문 정보
- curriculums: 커리큘럼 + 그래프 데이터 (JSONB)

TODO: Supabase 연결 후 실제 테이블과 매핑
"""

from app.models.user import User, RefreshToken
from app.models.paper import Paper
from app.models.curriculum import Curriculum

__all__ = [
    "User",
    "RefreshToken",
    "Paper",
    "Curriculum",
]
