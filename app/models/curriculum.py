"""Curriculum Models - 커리큘럼 관련 테이블 정의

TODO: Supabase PostgreSQL 테이블과 연동
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Column, JSON
from sqlalchemy import ARRAY, String


class Curriculum(SQLModel, table=True):
    """커리큘럼 모델
    
    TODO: 실제 DB 연결 시 구현
    - AI 생성 결과 저장
    - 상태 전이 관리
    - 그래프 데이터 JSONB 저장
    """
    __tablename__ = "curriculums"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    paper_id: UUID = Field(foreign_key="papers.id")
    title: Optional[str] = Field(default=None, max_length=200)
    status: str = Field(default="draft", max_length=20)  # draft, options_saved, generating, ready, failed
    
    # 옵션
    purpose: Optional[str] = Field(default=None, max_length=30)
    level: Optional[str] = Field(default=None, max_length=20)
    known_concepts: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))
    budgeted_time: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    preferred_resources: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))
    
    # AI 생성 결과
    graph_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # 집계 캐시
    node_count: int = Field(default=0)
    estimated_hours: float = Field(default=0.0)
    
    # 메타
    generation_started_at: Optional[datetime] = Field(default=None)
    generation_completed_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Keyword(SQLModel, table=True):
    """키워드/노드 모델
    
    TODO: 커리큘럼 그래프 노드 저장
    """
    __tablename__ = "keywords"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    curriculum_id: UUID = Field(foreign_key="curriculums.id", index=True)
    external_id: str = Field(max_length=50)  # 그래프 내 참조용 ID
    name: str = Field(max_length=200)
    description: Optional[str] = Field(default=None)
    importance: Optional[int] = Field(default=None, ge=1, le=10)
    layer: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Resource(SQLModel, table=True):
    """학습 리소스 모델
    
    TODO: 키워드별 학습 자료 저장
    """
    __tablename__ = "resources"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    keyword_id: UUID = Field(foreign_key="keywords.id", index=True)
    name: str = Field(max_length=300)
    url: Optional[str] = Field(default=None)
    type: str = Field(max_length=20)  # paper, article, video, code
    description: Optional[str] = Field(default=None)
    difficulty: Optional[int] = Field(default=None, ge=1, le=10)
    importance: Optional[int] = Field(default=None, ge=1, le=10)
    study_load_minutes: Optional[int] = Field(default=None)
    is_core: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class KeywordEdge(SQLModel, table=True):
    """키워드 관계 (엣지) 모델
    
    TODO: 그래프 엣지 저장
    """
    __tablename__ = "keyword_edges"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    curriculum_id: UUID = Field(foreign_key="curriculums.id", index=True)
    from_keyword_id: UUID = Field(foreign_key="keywords.id")
    to_keyword_id: UUID = Field(foreign_key="keywords.id")
    relationship: str = Field(default="prerequisite", max_length=50)


class LearningProgress(SQLModel, table=True):
    """학습 진행 상태 모델
    
    TODO: 사용자별 학습 진행 추적
    """
    __tablename__ = "learning_progress"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    curriculum_id: UUID = Field(foreign_key="curriculums.id", index=True)
    keyword_id: UUID = Field(foreign_key="keywords.id")
    status: str = Field(default="locked", max_length=20)  # locked, in_progress, completed, skipped
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
