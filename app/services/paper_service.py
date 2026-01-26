"""Paper service (stub).

Complex logic (upload to Supabase Storage, parsing PDFs, external search) will live here.
For now, API routes call these async stubs without implementing details.
"""

from __future__ import annotations

from typing import Any

from app import crud


async def upload_pdf_stub(*args: Any, **kwargs: Any) -> None:
    return None


async def submit_link_stub(*, url: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create dummy Paper + Curriculum rows for a link submission.

    This keeps business logic minimal while still persisting records to DB so
    Swagger Try-it-out can verify that data is actually inserted.
    """

    paper = await crud.papers.create_paper(
        title="URL에서 분석한 논문",
        authors=["Author from URL"],
        abstract="AI가 링크의 논문을 분석 중입니다. (더미 데이터)",
        language="english",
        source_url=url,
        pdf_storage_path=None,
    )

    curriculum = await crud.curriculums.create_curriculum(
        title="(더미) 링크 기반 커리큘럼",
        status="paper_attached",
        purpose=None,
        level=None,
        known_concepts=None,
        budgeted_time=None,
        preferred_resources=None,
        graph_data=None,
        node_count=0,
        estimated_hours=0.0,
    )

    await crud.junctions.add_curriculum_paper(
        curriculum_id=str(curriculum["id"]),
        paper_id=str(paper["id"]),
    )

    return paper, curriculum


async def search_by_title_stub(*args: Any, **kwargs: Any) -> None:
    return None

