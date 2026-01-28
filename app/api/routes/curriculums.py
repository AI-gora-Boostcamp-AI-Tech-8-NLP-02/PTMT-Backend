"""Curriculums Router - 커리큘럼 관련 API

TODO: 실제 구현 시
- DB CRUD 연동
- AI 기반 커리큘럼 생성 (비동기)
- 그래프 데이터 저장/조회
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app import crud
from app.crud.errors import CrudConfigError, NotFoundError
from app.schemas.common import ApiResponse, PaginationInfo
from app.schemas.curriculum import (
    BudgetedTime,
    CurriculumEdge,
    CurriculumGraphMeta,
    CurriculumGraphResponse,
    CurriculumListItem,
    CurriculumListResponse,
    CurriculumNode,
    CurriculumOptions,
    CurriculumPurpose,
    CurriculumResponse,
    CurriculumStatus,
    GenerationStartResponse,
    GenerationStatusResponse,
    PaperInfo,
    Resource,
    ResourceType,
    UserLevel,
)
from app.schemas.auth import MessageResponse
from app.schemas.user import UserResponse
from app.services import curriculum_generation_service

router = APIRouter(prefix="/curriculums", tags=["curriculums"])


# ===========================================
# 더미 데이터
# ===========================================

DUMMY_CURRICULUMS = [
    CurriculumListItem(
        id="curr-1",
        title="NLP 트랜스포머 입문",
        paper_title="Attention Is All You Need",
        status=CurriculumStatus.READY,
        created_at=datetime(2024, 1, 20, 10, 30),
        updated_at=datetime(2024, 1, 20, 12, 0),
        node_count=16,
        estimated_hours=24,
    ),
    CurriculumListItem(
        id="curr-2",
        title="딥러닝 기초 학습",
        paper_title="Deep Learning",
        status=CurriculumStatus.READY,
        created_at=datetime(2024, 1, 18, 9, 0),
        updated_at=datetime(2024, 1, 18, 14, 0),
        node_count=12,
        estimated_hours=18,
    ),
    CurriculumListItem(
        id="curr-3",
        title="CNN 이미지 분류",
        paper_title="ImageNet Classification with Deep CNNs",
        status=CurriculumStatus.READY,
        created_at=datetime(2024, 1, 15, 11, 0),
        updated_at=datetime(2024, 1, 15, 16, 0),
        node_count=10,
        estimated_hours=15,
    ),
]

DUMMY_GRAPH_NODES = [
    CurriculumNode(
        keyword_id="node-linear-algebra",
        keyword="선형대수",
        description="행렬 연산과 벡터 공간의 기초",
        importance=8,
        layer=1,
        resources=[
            Resource(
                resource_id="res-1",
                name="3Blue1Brown 선형대수",
                url="https://youtube.com/...",
                type=ResourceType.VIDEO,
                description="시각적으로 이해하는 선형대수",
                difficulty=3,
                importance=9,
                study_load_minutes=180,
                is_core=True,
            ),
        ],
    ),
    CurriculumNode(
        keyword_id="node-neural-network",
        keyword="신경망 기초",
        description="인공 신경망의 기본 구조와 학습 방법",
        importance=9,
        layer=2,
        resources=[
            Resource(
                resource_id="res-2",
                name="Deep Learning Book Chapter 6",
                url="https://deeplearningbook.org/",
                type=ResourceType.ARTICLE,
                description="Ian Goodfellow의 딥러닝 교과서",
                difficulty=6,
                importance=10,
                study_load_minutes=120,
                is_core=True,
            ),
        ],
    ),
    CurriculumNode(
        keyword_id="node-attention",
        keyword="Attention Mechanism",
        description="시퀀스 모델링에서의 어텐션 메커니즘",
        importance=10,
        layer=3,
        resources=[
            Resource(
                resource_id="res-3",
                name="Attention Is All You Need",
                url="https://arxiv.org/abs/1706.03762",
                type=ResourceType.PAPER,
                description="Transformer 원본 논문",
                difficulty=8,
                importance=10,
                study_load_minutes=180,
                is_core=True,
            ),
        ],
    ),
    CurriculumNode(
        keyword_id="node-transformer",
        keyword="Transformer",
        description="Self-Attention 기반 시퀀스 모델",
        importance=10,
        layer=4,
        resources=[
            Resource(
                resource_id="res-4",
                name="The Illustrated Transformer",
                url="https://jalammar.github.io/illustrated-transformer/",
                type=ResourceType.ARTICLE,
                description="트랜스포머 아키텍처 시각화 설명",
                difficulty=5,
                importance=9,
                study_load_minutes=60,
                is_core=True,
            ),
        ],
    ),
]

DUMMY_GRAPH_EDGES = [
    CurriculumEdge(from_keyword_id="node-linear-algebra", to_keyword_id="node-neural-network", relationship="prerequisite"),
    CurriculumEdge(from_keyword_id="node-neural-network", to_keyword_id="node-attention", relationship="prerequisite"),
    CurriculumEdge(from_keyword_id="node-attention", to_keyword_id="node-transformer", relationship="prerequisite"),
]


# ===========================================
# API 엔드포인트
# ===========================================

def _map_status_to_api(value: Optional[str]) -> CurriculumStatus:
    if value in {s.value for s in CurriculumStatus}:
        return CurriculumStatus(value)  # type: ignore[arg-type]
    # DB enum may contain values not present in API enum.
    mapping = {
        "options_set": CurriculumStatus.OPTIONS_SAVED,
        "paper_attached": CurriculumStatus.DRAFT,
    }
    return mapping.get(value or "", CurriculumStatus.DRAFT)


def _map_purpose_to_api(value: Optional[str]) -> Optional[CurriculumPurpose]:
    if value is None:
        return None
    if value in {p.value for p in CurriculumPurpose}:
        return CurriculumPurpose(value)  # type: ignore[arg-type]
    mapping = {
        "trend": CurriculumPurpose.TREND_CHECK,
        "code": CurriculumPurpose.CODE_IMPLEMENTATION,
        "prepare_exam": CurriculumPurpose.EXAM_PREPARATION,
    }
    return mapping.get(value)


def _map_level_to_api(value: Optional[str]) -> Optional[UserLevel]:
    if value is None:
        return None
    if value in {l.value for l in UserLevel}:
        return UserLevel(value)  # type: ignore[arg-type]
    mapping = {
        "worker": UserLevel.INDUSTRY,
    }
    return mapping.get(value)


def _map_purpose_to_db(value: CurriculumPurpose) -> str:
    mapping = {
        CurriculumPurpose.TREND_CHECK: "trend",
        CurriculumPurpose.CODE_IMPLEMENTATION: "code",
        CurriculumPurpose.EXAM_PREPARATION: "prepare_exam",
    }
    return mapping.get(value, value.value)


def _map_level_to_db(value: UserLevel) -> str:
    mapping = {
        UserLevel.INDUSTRY: "worker",
    }
    return mapping.get(value, value.value)


@router.get("", response_model=ApiResponse[CurriculumListResponse])
async def get_curriculums(
    status: Optional[str] = Query(None, description="필터링할 상태"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(10, ge=1, le=100, description="페이지당 항목 수"),
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[CurriculumListResponse]:
    """커리큘럼 목록 조회

    현재 로그인한 사용자의 커리큘럼 목록을 조회합니다.
    1. 현재 사용자의 커리큘럼 조회
    2. 상태별 필터링 (선택적)
    3. 페이지네이션
    """
    try:
        # 현재 사용자의 커리큘럼 조회
        rows, total = await crud.curriculums.get_curriculums_by_user(
            user_id=current_user.id,
            page=page,
            limit=limit,
        )
        
        # 상태별 필터링 (선택적)
        if status:
            rows = [r for r in rows if r.get("status") == status]
            total = len(rows)  # 필터링 후 총 개수 재계산
        
    except CrudConfigError:
        return ApiResponse.fail(
            "DB_NOT_CONFIGURED",
            "DB 설정이 필요합니다. (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)",
        )

    items: list[CurriculumListItem] = []
    for row in rows:
        curriculum_id = str(row.get("id", ""))
        paper_title = "Unknown Paper"
        try:
            linked_papers, _ = await crud.papers.get_paper_by_curr(
                curriculum_id=curriculum_id, page=1, limit=1
            )
            if linked_papers:
                paper_title = str(linked_papers[0].get("title") or paper_title)
        except Exception:
            pass

        items.append(
            CurriculumListItem(
                id=curriculum_id,
                title=str(row.get("title") or ""),
                paper_title=paper_title,
                status=_map_status_to_api(row.get("status")),
                created_at=row.get("created_at") or datetime.utcnow(),
                updated_at=row.get("updated_at") or row.get("created_at") or datetime.utcnow(),
                node_count=int(row.get("node_count") or 0),
                estimated_hours=float(row.get("estimated_hours") or 0),
            )
        )

    return ApiResponse.ok(
        CurriculumListResponse(
            items=items,
            pagination=PaginationInfo(
                page=page,
                limit=limit,
                total=total,
                has_more=(page * limit) < total,
            ),
        )
    )


@router.get("/{curriculum_id}", response_model=ApiResponse[CurriculumResponse])
async def get_curriculum(
    curriculum_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[CurriculumResponse]:
    """커리큘럼 단일 조회

    TODO: 실제 구현
    1. curriculum_id로 조회
    2. 권한 확인 (본인 소유)
    3. 상세 정보 반환
    """
    try:
        row = await crud.curriculums.get_curriculum(curriculum_id)
    except CrudConfigError:
        return ApiResponse.fail(
            "DB_NOT_CONFIGURED",
            "DB 설정이 필요합니다. (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)",
        )
    except NotFoundError:
        return ApiResponse.fail("CURRICULUM_NOT_FOUND", "커리큘럼을 찾을 수 없습니다.")

    paper = PaperInfo(id="paper-unknown", title="Unknown Paper")
    linked_papers, _ = await crud.papers.get_paper_by_curr(
        curriculum_id=curriculum_id, page=1, limit=1
    )
    if linked_papers:
        p = linked_papers[0]
        paper = PaperInfo(
            id=str(p.get("id", "paper-unknown")),
            title=str(p.get("title") or "Unknown Paper"),
            authors=p.get("authors"),
            abstract=p.get("abstract"),
        )

    preferred_resources = row.get("preferred_resources") or None
    pref: Optional[list[ResourceType]] = None
    if isinstance(preferred_resources, list):
        pref = []
        for r in preferred_resources:
            try:
                pref.append(ResourceType(str(r)))
            except Exception:
                continue

    bt = row.get("budgeted_time")
    budget: Optional[BudgetedTime] = None
    if isinstance(bt, dict) and "days" in bt and "daily_hours" in bt:
        budget = BudgetedTime(days=int(bt["days"]), daily_hours=float(bt["daily_hours"]))

    return ApiResponse.ok(
        CurriculumResponse(
            id=str(row.get("id", curriculum_id)),
            title=str(row.get("title") or ""),
            status=_map_status_to_api(row.get("status")),
            purpose=_map_purpose_to_api(row.get("purpose")),
            level=_map_level_to_api(row.get("level")),
            budgeted_time=budget,
            preferred_resources=pref,
            paper=paper,
            created_at=row.get("created_at") or datetime.utcnow(),
            updated_at=row.get("updated_at") or row.get("created_at") or datetime.utcnow(),
        )
    )


@router.delete("/{curriculum_id}", response_model=ApiResponse[MessageResponse])
async def delete_curriculum(
    curriculum_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[MessageResponse]:
    """커리큘럼 삭제

    TODO: 실제 구현
    1. curriculum_id로 조회
    2. 권한 확인
    3. 삭제 (cascade로 관련 데이터도 삭제)
    """
    try:
        await crud.curriculums.delete_curriculum(curriculum_id)
    except CrudConfigError:
        return ApiResponse.fail(
            "DB_NOT_CONFIGURED",
            "DB 설정이 필요합니다. (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)",
        )
    except NotFoundError:
        return ApiResponse.fail("CURRICULUM_NOT_FOUND", "커리큘럼을 찾을 수 없습니다.")
    return ApiResponse.ok(MessageResponse(message="커리큘럼이 삭제되었습니다."))


@router.post("/{curriculum_id}/options", response_model=ApiResponse[dict])
async def set_options(
    curriculum_id: str,
    options: CurriculumOptions,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[dict]:
    """커리큘럼 옵션 저장

    TODO: 실제 구현
    1. curriculum_id로 조회
    2. 권한 확인
    3. 옵션 저장
    4. 상태를 options_saved로 변경
    """
    try:
        await crud.curriculums.update_curriculum(
            curriculum_id,
            purpose=_map_purpose_to_db(options.purpose),
            level=_map_level_to_db(options.level),
            known_concepts=options.known_concepts,
            budgeted_time=options.budgeted_time.model_dump(),
            preferred_resources=[r.value for r in options.preferred_resources],
            status="options_set",
        )
    except CrudConfigError:
        return ApiResponse.fail(
            "DB_NOT_CONFIGURED",
            "DB 설정이 필요합니다. (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)",
        )
    except NotFoundError:
        return ApiResponse.fail("CURRICULUM_NOT_FOUND", "커리큘럼을 찾을 수 없습니다.")

    return ApiResponse.ok(
        {
            "curriculum_id": curriculum_id,
            "status": "options_set",
        }
    )


@router.post(
    "/{curriculum_id}/generate",
    response_model=ApiResponse[GenerationStartResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_generation(
    curriculum_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[GenerationStartResponse]:
    """커리큘럼 생성 시작 (비동기)

    TODO: 실제 구현
    1. curriculum_id로 조회
    2. 상태가 options_saved인지 확인
    3. 상태를 generating으로 변경
    4. 백그라운드 작업 시작 (AI 커리큘럼 생성)
    """
    try:
        # Minimal DB update + delegate heavy lifting to service stub.
        await crud.curriculums.update_curriculum(curriculum_id, status="generating")
    except CrudConfigError:
        return ApiResponse.fail(
            "DB_NOT_CONFIGURED",
            "DB 설정이 필요합니다. (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)",
        )
    except NotFoundError:
        return ApiResponse.fail("CURRICULUM_NOT_FOUND", "커리큘럼을 찾을 수 없습니다.")
    await curriculum_generation_service.start_generation(curriculum_id)
    return ApiResponse.ok(
        GenerationStartResponse(
            curriculum_id=curriculum_id,
            status="generating",
        )
    )


@router.get("/{curriculum_id}/status", response_model=ApiResponse[GenerationStatusResponse])
async def check_status(
    curriculum_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[GenerationStatusResponse]:
    """생성 상태 확인 (폴링용)"""
    await curriculum_generation_service.get_generation_status(curriculum_id)
    return ApiResponse.ok(
        GenerationStatusResponse(
            curriculum_id=curriculum_id,
            status=CurriculumStatus.READY,
            progress_percent=100,
            current_step="완료!",
        )
    )


@router.get("/{curriculum_id}/graph", response_model=ApiResponse[CurriculumGraphResponse])
async def get_graph(
    curriculum_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[CurriculumGraphResponse]:
    """커리큘럼 그래프 조회"""
    await curriculum_generation_service.get_graph(curriculum_id)
    return ApiResponse.ok(
        CurriculumGraphResponse(
            meta=CurriculumGraphMeta(
                curriculum_id=curriculum_id,
                paper_id="paper-1",
                paper_title="Attention Is All You Need",
                paper_authors=["Vaswani et al."],
                created_at=datetime(2024, 1, 20, 10, 30),
                total_study_time_hours=24.5,
                total_nodes=len(DUMMY_GRAPH_NODES),
            ),
            nodes=DUMMY_GRAPH_NODES,
            edges=DUMMY_GRAPH_EDGES,
        )
    )

