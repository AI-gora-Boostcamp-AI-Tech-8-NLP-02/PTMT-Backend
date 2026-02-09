"""Junction Table Models - 관계 테이블 정의

Junction tables for many-to-many relationships:
- user_papers: User와 Paper 간의 관계
- user_curriculums: User와 Curriculum 간의 관계
- curriculum_papers: Curriculum과 Paper 간의 관계
"""

from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel


class UserPaper(SQLModel, table=True):
    """User-Paper 관계 (Many-to-Many)
    
    사용자가 업로드하거나 조회한 논문
    """
    __tablename__ = "user_papers"

    user_id: UUID = Field(foreign_key="users.id", primary_key=True)
    paper_id: UUID = Field(foreign_key="papers.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserCurriculum(SQLModel, table=True):
    """User-Curriculum 관계 (Many-to-Many)
    
    사용자가 생성하거나 조회한 커리큘럼
    """
    __tablename__ = "user_curriculums"

    user_id: UUID = Field(foreign_key="users.id", primary_key=True)
    curriculum_id: UUID = Field(foreign_key="curriculums.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CurriculumPaper(SQLModel, table=True):
    """Curriculum-Paper 관계 (Many-to-Many)
    
    커리큘럼과 연결된 논문
    """
    __tablename__ = "curriculum_papers"

    curriculum_id: UUID = Field(foreign_key="curriculums.id", primary_key=True)
    paper_id: UUID = Field(foreign_key="papers.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
