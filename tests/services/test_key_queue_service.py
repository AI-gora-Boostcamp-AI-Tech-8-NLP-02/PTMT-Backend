import asyncio
import time

import pytest

from app.services.key_queue_service import KeyQueueService


@pytest.mark.asyncio
async def test_fifo_and_round_robin_assignment() -> None:
    service = KeyQueueService(total_keys=2, cooldown_seconds=0)

    first_slot = await service.acquire_slot(task_type="test", task_id="job-1")
    second_slot = await service.acquire_slot(task_type="test", task_id="job-2")
    assert first_slot == 1
    assert second_slot == 2

    results: list[tuple[str, int]] = []

    async def wait_for_slot(job_id: str) -> int:
        slot = await service.acquire_slot(task_type="test", task_id=job_id)
        results.append((job_id, slot))
        return slot

    task_3 = asyncio.create_task(wait_for_slot("job-3"))
    task_4 = asyncio.create_task(wait_for_slot("job-4"))

    await asyncio.sleep(0.05)
    await service.release_slot(first_slot)
    await asyncio.sleep(0.05)
    await service.release_slot(second_slot)

    await asyncio.wait_for(asyncio.gather(task_3, task_4), timeout=1.0)

    assert results == [("job-3", 1), ("job-4", 2)]


@pytest.mark.asyncio
async def test_cooldown_blocks_reassignment() -> None:
    service = KeyQueueService(total_keys=1, cooldown_seconds=1)

    slot = await service.acquire_slot(task_type="test", task_id="job-1")
    await service.release_slot(slot)

    started_at = time.monotonic()
    reassigned_slot = await service.acquire_slot(task_type="test", task_id="job-2")
    elapsed = time.monotonic() - started_at

    assert reassigned_slot == 1
    assert elapsed >= 0.9


@pytest.mark.asyncio
async def test_release_curriculum_slot_by_lease() -> None:
    service = KeyQueueService(total_keys=1, cooldown_seconds=0)

    slot = await service.acquire_slot(
        task_type="curriculum_generation",
        task_id="curr-1",
        curriculum_id="curr-1",
    )
    assert slot == 1

    released = await service.release_curriculum_slot("curr-1")
    assert released is True

    next_slot = await service.acquire_slot(task_type="test", task_id="job-2")
    assert next_slot == 1


@pytest.mark.asyncio
async def test_cancelled_waiting_task_removed_from_queue() -> None:
    service = KeyQueueService(total_keys=1, cooldown_seconds=0)

    slot = await service.acquire_slot(task_type="test", task_id="job-1")

    waiting_task = asyncio.create_task(
        service.acquire_slot(task_type="test", task_id="job-2")
    )
    await asyncio.sleep(0.05)
    waiting_task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await waiting_task

    snapshot = await service.get_snapshot()
    assert snapshot["waiting_jobs"] == 0

    await service.release_slot(slot)
