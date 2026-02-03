"""Curriculum Schemas - 커리큘럼 관련 요청/응답 스키마"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import PaginationInfo


# ===========================================
# Enums
# ===========================================

class CurriculumStatus(str, Enum):
    """커리큘럼 상태"""
    DRAFT = "draft"
    OPTIONS_SAVED = "options_saved"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class CurriculumPurpose(str, Enum):
    """학습 목적"""
    DEEP_RESEARCH = "deep_research"
    SIMPLE_STUDY = "simple_study"
    TREND_CHECK = "trend_check"
    CODE_IMPLEMENTATION = "code_implementation"
    EXAM_PREPARATION = "exam_preparation"


class UserLevel(str, Enum):
    """사용자 수준"""
    NON_MAJOR = "non_major"
    BACHELOR = "bachelor"
    MASTER = "master"
    RESEARCHER = "researcher"
    INDUSTRY = "industry"


class ResourceType(str, Enum):
    """리소스 타입"""
    PAPER = "paper"
    ARTICLE = "article"
    VIDEO = "video"
    CODE = "code"


# ===========================================
# Request Schemas
# ===========================================

class BudgetedTime(BaseModel):
    """학습 시간 예산"""
    days: int
    daily_hours: float


class CurriculumOptions(BaseModel):
    """커리큘럼 옵션 설정"""
    purpose: CurriculumPurpose
    level: UserLevel
    known_concepts: List[str]  # keyword_id 배열
    budgeted_time: BudgetedTime
    preferred_resources: List[ResourceType]


class CurriculumImportRequest(BaseModel):
    """커리큘럼 import 요청"""
    curriculum_id: str
    title: str
    graph: dict  # nodes, edges 포함
    created_at: str


# ===========================================
# Response Schemas
# ===========================================

class CurriculumListItem(BaseModel):
    """커리큘럼 목록 아이템"""
    id: str
    title: str
    paper_title: str
    status: CurriculumStatus
    created_at: datetime
    updated_at: datetime
    node_count: int
    estimated_hours: float


class CurriculumListResponse(BaseModel):
    """커리큘럼 목록 응답"""
    items: List[CurriculumListItem]
    pagination: PaginationInfo


class PaperInfo(BaseModel):
    """논문 정보 (커리큘럼 상세에 포함)"""
    id: str
    title: str
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None


class CurriculumResponse(BaseModel):
    """커리큘럼 단일 조회 응답"""
    id: str
    title: str
    status: CurriculumStatus
    purpose: Optional[CurriculumPurpose] = None
    level: Optional[UserLevel] = None
    budgeted_time: Optional[BudgetedTime] = None
    preferred_resources: Optional[List[ResourceType]] = None
    paper: PaperInfo
    created_at: datetime
    updated_at: datetime


class GenerationStartResponse(BaseModel):
    """커리큘럼 생성 시작 응답"""
    curriculum_id: str
    status: str = "generating"


class GenerationStatusResponse(BaseModel):
    """커리큘럼 생성 상태 응답"""
    curriculum_id: str
    status: CurriculumStatus
    progress_percent: float | None = None  # 진행률 미지원 시 None
    current_step: str


class CurriculumImportResponse(BaseModel):
    """커리큘럼 import 응답"""
    curriculum_id: str
    status: str = "ready"


# ===========================================
# Graph Schemas
# ===========================================

class Resource(BaseModel):
    """학습 리소스"""
    resource_id: str
    name: str
    url: Optional[str] = None
    type: ResourceType
    description: str
    difficulty: int  # 1-10
    importance: int  # 1-10
    study_load_minutes: int
    is_core: bool


class CurriculumNode(BaseModel):
    """커리큘럼 그래프 노드"""
    keyword_id: str
    keyword: str
    description: str
    importance: int
    is_keyword_necessary: bool
    is_resource_sufficient: bool
    resources: List[Resource]


class CurriculumEdge(BaseModel):
    """커리큘럼 그래프 엣지"""
    end_keyword_id: str
    start_keyword_id: str


class CurriculumGraphMeta(BaseModel):
    """커리큘럼 그래프 메타 정보"""
    curriculum_id: str
    paper_id: str
    paper_title: str
    paper_authors: Optional[List[str]] = None
    summarize: str
    created_at: datetime
    total_study_time_hours: float
    total_nodes: int

class CurriculumGraphResponse(BaseModel):
    """커리큘럼 그래프 응답"""
    meta: CurriculumGraphMeta
    nodes: List[CurriculumNode]
    edges: List[CurriculumEdge]
    first_node_order: List[str]
