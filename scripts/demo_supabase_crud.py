from __future__ import annotations

import json
from pathlib import Path
import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

# Ensure project root is on sys.path when executed as a script:
#   python scripts/demo_supabase_crud.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.crud import curriculums, get_supabase_client, junctions, papers, refresh_tokens, users
from app.crud.errors import CrudError
from app.crud.supabase_client import require_supabase_config


def _pp(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, default=str)


def _title(msg: str) -> None:
    print("\n" + "=" * 80)
    print(msg)
    print("=" * 80)


def _step(msg: str) -> None:
    print(f"\n- {msg}")


async def main() -> int:
    run_id = f"demo-{uuid.uuid4().hex[:8]}"
    _title(f"Supabase CRUD Demo (run_id={run_id})")

    # -------------------------
    # Config + client smoke test
    # -------------------------
    _title("0) Configuration check")
    try:
        url, _key = require_supabase_config()
    except Exception as e:
        print("Missing config. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")
        print(f"Error: {e}")
        return 2
    print(f"SUPABASE_URL: {url}")

    _title("1) Supabase client smoke test")
    client = await get_supabase_client()
    try:
        # Just confirm PostgREST is reachable by reading 1 row from a known table.
        req = client.table("users").select("id").limit(1)
        resp = await req.execute()
        print(f"users table reachable. rows={len(resp.data or [])}")
    except Exception as e:
        print("Failed to query Supabase. Check URL/key, network, and PostgREST availability.")
        print(f"Error: {e}")
        return 3

    # -------------------------
    # Users
    # -------------------------
    _title("2) users CRUD")
    email = f"{run_id}-{uuid.uuid4().hex}@example.com"
    _step(f"create_user(email={email})")
    user = await users.create_user(email=email, password_hash="hash", name=f"Demo User {run_id}")
    user_id = user["id"]
    print(_pp(user))

    _step(f"get_user(id={user_id})")
    print(_pp(await users.get_user(user_id)))

    _step("update_user(name=...)")
    print(_pp(await users.update_user(user_id, name=f"Demo User Updated {run_id}")))

    # -------------------------
    # Papers
    # -------------------------
    _title("3) papers CRUD")
    _step("create_paper(title=...)")
    paper = await papers.create_paper(
        title=f"Demo Paper {run_id}",
        authors=["Alice", "Bob"],
        abstract=f"Demo abstract ({run_id})",
        language="english",
        source_url="https://example.com",
        pdf_storage_path=f"papers/{run_id}/paper.pdf",
    )
    paper_id = paper["id"]
    print(_pp(paper))

    _step(f"get_paper(id={paper_id})")
    print(_pp(await papers.get_paper(paper_id)))

    _step("update_paper(title=...)")
    print(_pp(await papers.update_paper(paper_id, title=f"Demo Paper Updated {run_id}")))

    # -------------------------
    # Curriculums
    # -------------------------
    _title("4) curriculums CRUD")
    _step("create_curriculum(title=..., status=draft, purpose=simple_study, level=bachelor)")
    curriculum = await curriculums.create_curriculum(
        title=f"Demo Curriculum {run_id}",
        status="draft",
        purpose="simple_study",
        level="bachelor",
        known_concepts=["linear_algebra", "probability"],
        budgeted_time={"days": 7, "daily_hours": 2},
        preferred_resources=["paper", "article"],
        graph_data={"meta": {"run_id": run_id}, "nodes": [], "edges": []},
        node_count=0,
        estimated_hours=0.0,
    )
    curriculum_id = curriculum["id"]
    print(_pp(curriculum))

    _step(f"get_curriculum(id={curriculum_id})")
    print(_pp(await curriculums.get_curriculum(curriculum_id)))

    _step("update_curriculum(status=ready)")
    print(_pp(await curriculums.update_curriculum(curriculum_id, status="ready")))

    # -------------------------
    # Junction tables
    # -------------------------
    _title("5) junction tables")
    _step("add_user_paper(user_id, paper_id)")
    print(_pp(await junctions.add_user_paper(user_id=user_id, paper_id=paper_id)))

    _step("add_user_curriculum(user_id, curriculum_id)")
    print(_pp(await junctions.add_user_curriculum(user_id=user_id, curriculum_id=curriculum_id)))

    _step("add_curriculum_paper(curriculum_id, paper_id)")
    print(_pp(await junctions.add_curriculum_paper(curriculum_id=curriculum_id, paper_id=paper_id)))

    _step("list_user_papers(user_id)")
    rows, total = await junctions.list_user_papers(user_id=user_id, page=1, limit=50)
    print(f"total={total}")
    print(_pp(rows))

    _step("list_user_curriculums(user_id)")
    rows, total = await junctions.list_user_curriculums(user_id=user_id, page=1, limit=50)
    print(f"total={total}")
    print(_pp(rows))

    _step("list_curriculum_papers(curriculum_id)")
    rows, total = await junctions.list_curriculum_papers(curriculum_id=curriculum_id, page=1, limit=50)
    print(f"total={total}")
    print(_pp(rows))

    _title("5b) relationship helpers (after linking)")
    _step("papers.get_paper_by_user(user_id)")
    rows, total = await papers.get_paper_by_user(user_id=str(user_id), page=1, limit=50)
    print(f"total={total}")
    print(_pp(rows))
    _step("users.get_user_by_paper(paper_id)")
    rows, total = await users.get_user_by_paper(paper_id=str(paper_id), page=1, limit=50)
    print(f"total={total}")
    print(_pp(rows))
    _step("curriculums.get_curr_by_user(user_id)")
    rows, total = await curriculums.get_curr_by_user(user_id=str(user_id), page=1, limit=50)
    print(f"total={total}")
    print(_pp(rows))
    _step("users.get_user_by_curr(curriculum_id)")
    rows, total = await users.get_user_by_curr(curriculum_id=str(curriculum_id), page=1, limit=50)
    print(f"total={total}")
    print(_pp(rows))
    _step("curriculums.get_curr_by_paper(paper_id)")
    rows, total = await curriculums.get_curr_by_paper(paper_id=str(paper_id), page=1, limit=50)
    print(f"total={total}")
    print(_pp(rows))
    _step("papers.get_paper_by_curr(curriculum_id)")
    rows, total = await papers.get_paper_by_curr(curriculum_id=str(curriculum_id), page=1, limit=50)
    print(f"total={total}")
    print(_pp(rows))

    # -------------------------
    # Refresh tokens
    # -------------------------
    _title("6) refresh_tokens CRUD")
    _step("create_refresh_token(user_id)")
    token = await refresh_tokens.create_refresh_token(
        user_id=user_id,
        token_hash=f"hash-{run_id}-{uuid.uuid4().hex}",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    token_id = token["id"]
    print(_pp(token))

    _step("revoke_refresh_token(token_id)")
    print(_pp(await refresh_tokens.revoke_refresh_token(token_id)))

    # -------------------------
    # Summary
    # -------------------------
    _title("Summary (records kept)")
    summary = {
        "run_id": run_id,
        "user_id": user_id,
        "paper_id": paper_id,
        "curriculum_id": curriculum_id,
        "refresh_token_id": token_id,
        "note": "Records are kept by default. Use these ids to inspect in Supabase dashboard.",
    }
    print(_pp(summary))
    print("\nTo clean up manually later (example):")
    print(
        _pp(
            {
                "python": [
                    "from app.crud import users, papers, curriculums",
                    f"users.delete_user('{user_id}')  # cascades refresh_tokens + junctions via FK",
                    f"papers.delete_paper('{paper_id}')",
                    f"curriculums.delete_curriculum('{curriculum_id}')",
                ]
            }
        )
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except CrudError as e:
        print("\nCRUD error:")
        print(str(e))
        raise SystemExit(1)

