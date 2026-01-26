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

@router.get("", response_model=ApiResponse[CurriculumListResponse])
async def get_curriculums(
    status: Optional[str] = Query(None, description="필터링할 상태"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(10, ge=1, le=100, description="페이지당 항목 수"),
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[CurriculumListResponse]:
    """커리큘럼 목록 조회

    TODO: 실제 구현
    1. 현재 사용자의 커리큘럼 조회
    2. 상태별 필터링
    3. 페이지네이션
    """
    # TODO: DB 조회
    # query = select(Curriculum).where(Curriculum.user_id == current_user.id)
    # if status:
    #     query = query.where(Curriculum.status == status)
    # curriculums = await db.exec(query.offset((page-1)*limit).limit(limit))

    # 더미 응답
    items = DUMMY_CURRICULUMS
    if status:
        items = [c for c in items if c.status.value == status]

    return ApiResponse.ok(
        CurriculumListResponse(
            items=items,
            pagination=PaginationInfo(
                page=page,
                limit=limit,
                total=len(items),
                has_more=False,
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
    # TODO: DB 조회
    # curriculum = await crud.curriculum.get(db, id=curriculum_id)
    # if not curriculum:
    #     return ApiResponse.fail("CURRICULUM_NOT_FOUND", "커리큘럼을 찾을 수 없습니다.")
    # if curriculum.user_id != current_user.id:
    #     return ApiResponse.fail("FORBIDDEN", "접근 권한이 없습니다.")

    # 더미 응답
    return ApiResponse.ok(
        CurriculumResponse(
            id=curriculum_id,
            title="NLP 트랜스포머 입문",
            status=CurriculumStatus.READY,
            purpose=CurriculumPurpose.DEEP_RESEARCH,
            level=UserLevel.MASTER,
            budgeted_time=BudgetedTime(days=14, daily_hours=2),
            preferred_resources=[ResourceType.PAPER, ResourceType.ARTICLE],
            paper=PaperInfo(
                id="paper-1",
                title="Attention Is All You Need",
                authors=["Vaswani et al."],
                abstract="트랜스포머 아키텍처를 제안한 논문...",
            ),
            created_at=datetime(2024, 1, 20, 10, 30),
            updated_at=datetime(2024, 1, 20, 12, 0),
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
    # TODO: DB 삭제
    # curriculum = await crud.curriculum.get(db, id=curriculum_id)
    # if not curriculum:
    #     return ApiResponse.fail("CURRICULUM_NOT_FOUND", "커리큘럼을 찾을 수 없습니다.")
    # await crud.curriculum.delete(db, id=curriculum_id)

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
    # TODO: DB 업데이트
    # curriculum = await crud.curriculum.get(db, id=curriculum_id)
    # if not curriculum:
    #     return ApiResponse.fail("CURRICULUM_NOT_FOUND", "커리큘럼을 찾을 수 없습니다.")
    # await crud.curriculum.update(db, id=curriculum_id,
    #     purpose=options.purpose,
    #     level=options.level,
    #     known_concepts=options.known_concepts,
    #     budgeted_time=options.budgeted_time.model_dump(),
    #     preferred_resources=[r.value for r in options.preferred_resources],
    #     status="options_saved"
    # )

    return ApiResponse.ok(
        {
            "curriculum_id": curriculum_id,
            "status": "options_saved",
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

