"""Curriculum Model - 커리큘럼 테이블 정의

RDB 설계:
- 그래프 데이터(nodes, edges, resources)는 graph_data JSONB 컬럼에 통합 저장
- 별도 테이블로 정규화하지 않음 (데모용 단순화)

TODO: Supabase PostgreSQL 테이블과 연동
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Column, JSON
from sqlalchemy import ARRAY, String


class Curriculum(SQLModel, table=True):
    """커리큘럼 모델
    
    graph_data JSON 구조:
    {
        "meta": {
            "paper_title": "...",
            "paper_authors": ["..."],
            "total_study_time_hours": 24.5,
            "total_nodes": 16
        },
        "nodes": [
            {
                "keyword_id": "node-1",
                "keyword": "Transformer",
                "description": "...",
                "importance": 10,
                "layer": 5,
                "resources": [
                    {
                        "resource_id": "res-1",
                        "name": "...",
                        "url": "...",
                        "type": "article",
                        "difficulty": 5,
                        "importance": 9,
                        "study_load_minutes": 60,
                        "is_core": true
                    }
                ]
            }
        ],
        "edges": [
            {
                "from_keyword_id": "node-1",
                "to_keyword_id": "node-2",
                "relationship": "prerequisite"
            }
        ]
    }
    """
    __tablename__ = "curriculums"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: Optional[str] = Field(default=None, max_length=200)
    status: str = Field(default="draft", max_length=20)  # draft, options_saved, generating, ready, failed
    
    # 사용자 설정 옵션
    purpose: Optional[str] = Field(default=None, max_length=30)  # deep_research, simple_study, etc.
    level: Optional[str] = Field(default=None, max_length=20)  # non_major, bachelor, master, etc.
    known_concepts: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))
    budgeted_time: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # { days, daily_hours }
    preferred_resources: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))  # paper, article, video, code
    
    # AI 생성 결과 (그래프 전체를 JSON으로 저장)
    graph_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # 집계 캐시 (빠른 조회용)
    node_count: int = Field(default=0)
    estimated_hours: float = Field(default=0.0)
    
    # 타임스탬프
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
