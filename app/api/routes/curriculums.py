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
    CurriculumImportRequest,
    CurriculumImportResponse,
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
        is_keyword_necessary=True,
        is_resource_sufficient=True,
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
        is_keyword_necessary=True,
        is_resource_sufficient=True,
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
        is_keyword_necessary=True,
        is_resource_sufficient=True,
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
        is_keyword_necessary=True,
        is_resource_sufficient=True,
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
    CurriculumEdge(start_keyword_id="node-linear-algebra", end_keyword_id="node-neural-network"),
    CurriculumEdge(start_keyword_id="node-neural-network", end_keyword_id="node-attention"),
    CurriculumEdge(start_keyword_id="node-attention", end_keyword_id="node-transformer"),
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
    
    # 외부 API 호출
    try:
        result = await curriculum_generation_service.start_generation(curriculum_id)
        
        # 결과 확인: curriculum_id가 일치하고 success가 true이고 status가 generating이면
        if result:
            result_success = result.get("success")
            
            if (result_success is True):
                return ApiResponse.ok(
                    GenerationStartResponse(
                        curriculum_id=curriculum_id,
                        status="generating",
                    )
                )
        
        # 조건에 맞지 않으면 실패 처리
        await crud.curriculums.update_curriculum(curriculum_id, status="failed")
        return ApiResponse.fail(
            "GENERATION_FAILED",
            "커리큘럼 생성 시작에 실패했습니다. 외부 API 응답이 올바르지 않습니다.",
        )
        
    except Exception as e:
        # 외부 API 호출 실패 시
        await crud.curriculums.update_curriculum(curriculum_id, status="failed")
        return ApiResponse.fail(
            "GENERATION_FAILED",
            f"커리큘럼 생성 시작에 실패했습니다: {str(e)}",
        )


@router.get("/{curriculum_id}/status", response_model=ApiResponse[GenerationStatusResponse])
async def check_status(
    curriculum_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[GenerationStatusResponse]:
    """생성 상태 확인 (폴링용)"""
    try:
        curriculum = await crud.curriculums.get_curriculum(curriculum_id)
    except CrudConfigError:
        return ApiResponse.fail(
            "DB_NOT_CONFIGURED",
            "DB 설정이 필요합니다. (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)",
        )
    except NotFoundError:
        return ApiResponse.fail("CURRICULUM_NOT_FOUND", "커리큘럼을 찾을 수 없습니다.")
    
    # DB에서 가져온 상태 매핑
    db_status = curriculum.get("status", "draft")
    api_status = _map_status_to_api(db_status)
    
    # 상태에 따른 단계 설정
    current_step = "초기화 중"
    
    if api_status == CurriculumStatus.DRAFT:
        current_step = "논문 업로드 완료"
    elif api_status == CurriculumStatus.OPTIONS_SAVED:
        current_step = "옵션 설정 완료"
    elif api_status == CurriculumStatus.GENERATING:
        current_step = "AI가 커리큘럼을 생성하는 중..."
    elif api_status == CurriculumStatus.READY:
        current_step = "완료!"
    elif api_status == CurriculumStatus.FAILED:
        current_step = "생성 실패"
    
    return ApiResponse.ok(
        GenerationStatusResponse(
            curriculum_id=curriculum_id,
            status=api_status,
            progress_percent=None,
            current_step=current_step,
        )
    )


@router.get("/{curriculum_id}/graph", response_model=ApiResponse[CurriculumGraphResponse])
async def get_graph(
    curriculum_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[CurriculumGraphResponse]:
    """커리큘럼 그래프 조회"""
    try:
        curriculum = await crud.curriculums.get_curriculum(curriculum_id)
    except CrudConfigError:
        return ApiResponse.fail(
            "DB_NOT_CONFIGURED",
            "DB 설정이 필요합니다. (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)",
        )
    except NotFoundError:
        return ApiResponse.fail("CURRICULUM_NOT_FOUND", "커리큘럼을 찾을 수 없습니다.")
    
    # graph_data 확인
    graph_data = curriculum.get("graph_data")
    if not graph_data or not isinstance(graph_data, dict):
        return ApiResponse.fail(
            "GRAPH_NOT_READY",
            "커리큘럼 그래프가 아직 생성되지 않았습니다.",
        )
    
    paper_id = "unknown"
    paper_title = "Unknown Paper"
    paper_authors = []
    summarize = "Unknown Summary"
    
    try:
        linked_papers, _ = await crud.papers.get_paper_by_curr(
            curriculum_id=curriculum_id, page=1, limit=1
        )
        print(linked_papers[0].keys())
        if linked_papers:
            p = linked_papers[0]
            paper_id = str(p.get("id", "unknown"))
            paper_title = str(p.get("title") or "Unknown Paper")
            paper_authors = p.get("authors") or []
            summarize = p.get("summarize") or "Unknown Summary"
    except Exception:
        pass


    # 그래프 데이터 파싱
    nodes_data = graph_data.get("nodes", [])
    edges_data = graph_data.get("edges", [])
    first_node_order = graph_data.get("first_node_order", [])
    
    # 노드 파싱
    nodes = []
    for node_dict in nodes_data:
        if not isinstance(node_dict, dict):
            continue
        
        # 리소스 파싱
        resources = []
        for res_dict in node_dict.get("resources", []):
            if not isinstance(res_dict, dict):
                continue
            try:
                resources.append(
                    Resource(
                        url=res_dict.get("url"),
                        type=ResourceType(res_dict.get("type", "article")),
                        difficulty=int(res_dict.get("difficulty", 5)),
                        importance=int(res_dict.get("importance", 5)),
                        study_load_minutes=int(res_dict.get("study_load_minutes", 0)),
                        resource_id=str(res_dict.get("resource_id", "")),
                        is_core=bool(res_dict.get("is_necessary", False)),
                        name=str(res_dict.get("resource_name", "")),
                        description=str(res_dict.get("description", "")),
                    )
                )
            except Exception:
                continue
        
        try:
            nodes.append(
                CurriculumNode(
                    keyword=str(node_dict.get("keyword", "")),
                    resources=resources,
                    keyword_id=str(node_dict.get("keyword_id", "")),
                    description=str(node_dict.get("description", "")),
                    importance=int(node_dict.get("keyword_importance", 5)),
                    is_keyword_necessary=bool(node_dict.get("is_keyword_necessary", False)),
                    is_resource_sufficient=bool(node_dict.get("is_resource_sufficient", False)),
                )
            )
        except Exception:
            continue
    
    # 엣지 파싱
    edges = []
    for edge_dict in edges_data:
        if not isinstance(edge_dict, dict):
            continue
        try:
            edges.append(
                CurriculumEdge(
                    end_keyword_id=str(edge_dict.get("end", "")),
                    start_keyword_id=str(edge_dict.get("start", "")),
                )
            )
        except Exception:
            continue
    
    # 메타 정보 계산
    total_study_time_hours = float(curriculum.get("estimated_hours", 0.0))
    total_nodes = len(nodes)
    
    return ApiResponse.ok(
        CurriculumGraphResponse(
            meta=CurriculumGraphMeta(
                curriculum_id=curriculum_id,
                paper_id=paper_id,
                paper_title=paper_title,
                paper_authors=paper_authors,
                summarize=summarize,
                created_at=curriculum.get("created_at") or datetime.utcnow(),
                total_study_time_hours=total_study_time_hours,
                total_nodes=total_nodes,
            ),
            nodes=nodes,
            edges=edges,
            first_node_order=first_node_order,
        )
    )


@router.post(
    "/import",
    response_model=ApiResponse[CurriculumImportResponse],
    status_code=status.HTTP_201_CREATED,
)
async def import_curriculum(
    request: CurriculumImportRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiResponse[CurriculumImportResponse]:
    """커리큘럼 그래프 import
    
    외부에서 생성된 커리큘럼 그래프를 DB에 저장합니다.
    
    1. curriculum_id로 커리큘럼 조회
    2. graph 데이터를 graph_data 필드에 저장
    3. 상태를 ready로 변경
    4. 노드 수와 예상 학습 시간 계산 (선택적)
    """
    try:
        # curriculum_id로 커리큘럼 조회
        curriculum = await crud.curriculums.get_curriculum(request.curriculum_id)
    except CrudConfigError:
        return ApiResponse.fail(
            "DB_NOT_CONFIGURED",
            "DB 설정이 필요합니다. (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)",
        )
    except NotFoundError:
        return ApiResponse.fail(
            "CURRICULUM_NOT_FOUND",
            f"커리큘럼을 찾을 수 없습니다: {request.curriculum_id}",
        )
    
    # 필수 필드 확인
    if not request.graph:
        return ApiResponse.fail(
            "INVALID_REQUEST",
            "curriculum_id, graph는 필수입니다.",
        )
    
    # 노드 수 계산
    nodes = request.graph.get("nodes", [])
    node_count = len(nodes) if isinstance(nodes, list) else 0
    
    # 예상 학습 시간 계산 (선택적)
    estimated_hours = 0.0
    if isinstance(nodes, list):
        for node in nodes:
            if isinstance(node, dict):
                resources = node.get("resources", [])
                if isinstance(resources, list):
                    for resource in resources:
                        if isinstance(resource, dict):
                            minutes = resource.get("study_load_minutes", 0)
                            estimated_hours += minutes / 60.0
    
    # graph 데이터 저장 및 상태 업데이트
    try:
        await crud.curriculums.update_curriculum(
            request.curriculum_id,
            title=request.title,
            graph_data=request.graph,
            status="ready",
            node_count=node_count,
            estimated_hours=estimated_hours,
        )
    except CrudConfigError:
        return ApiResponse.fail(
            "DB_NOT_CONFIGURED",
            "DB 설정이 필요합니다. (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)",
        )
    except NotFoundError:
        return ApiResponse.fail(
            "CURRICULUM_NOT_FOUND",
            f"커리큘럼을 찾을 수 없습니다: {request.curriculum_id}",
        )
    except Exception as e:
        return ApiResponse.fail(
            "INTERNAL_SERVER_ERROR",
            f"서버 오류가 발생했습니다: {str(e)}",
        )
    
    return ApiResponse.ok(
        CurriculumImportResponse(
            curriculum_id=request.curriculum_id,
            status="ready",
        )
    )

