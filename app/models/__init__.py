"""SQLModel Models - 데이터베이스 모델 정의

TODO: Supabase 연결 후 실제 테이블과 매핑
현재는 더미 모델로 구조만 정의
"""

from app.models.user import User
from app.models.paper import Paper
from app.models.curriculum import Curriculum, Keyword, Resource, KeywordEdge, LearningProgress

__all__ = [
    "User",
    "Paper",
    "Curriculum",
    "Keyword",
    "Resource",
    "KeywordEdge",
    "LearningProgress",
]
