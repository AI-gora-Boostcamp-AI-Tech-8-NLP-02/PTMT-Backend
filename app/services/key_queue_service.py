"""In-memory key slot queue service.

Manages shared key slots with FIFO waiting queue, round-robin assignment,
and cooldown handling.
"""

from __future__ import annotations

import asyncio
import math
import time
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional

from app.core.config import settings


SLOT_READY = "ready"
SLOT_BUSY = "busy"
SLOT_COOLDOWN = "cooldown"


@dataclass(slots=True)
class QueueTicket:
    """Represents one waiting job in FIFO queue."""

    ticket_id: str
    task_type: str
    task_id: Optional[str]


@dataclass(slots=True)
class KeySlot:
    """Represents one key slot state."""

    slot_number: int
    status: str = SLOT_READY
    cooldown_until: float = 0.0
    current_task_type: Optional[str] = None
    current_task_id: Optional[str] = None


class KeyQueueService:
    """Shared queue for key-slot assignment with cooldown support."""

    def __init__(self, total_keys: int = 5, cooldown_seconds: int = 30) -> None:
        if total_keys < 1:
            raise ValueError("total_keys must be >= 1")
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be >= 0")

        self._total_keys = total_keys
        self._cooldown_seconds = cooldown_seconds
        self._slots: list[KeySlot] = [
            KeySlot(slot_number=index + 1) for index in range(total_keys)
        ]
        self._wait_queue: Deque[QueueTicket] = deque()
        self._curriculum_leases: dict[str, int] = {}
        self._condition = asyncio.Condition()
        self._round_robin_cursor = -1

    def _now(self) -> float:
        return time.monotonic()

    def _get_slot_by_number(self, slot_number: int) -> Optional[KeySlot]:
        if slot_number < 1 or slot_number > self._total_keys:
            return None
        return self._slots[slot_number - 1]

    def _refresh_slots_locked(self, now: float) -> None:
        for slot in self._slots:
            if slot.status == SLOT_COOLDOWN and slot.cooldown_until <= now:
                slot.status = SLOT_READY
                slot.cooldown_until = 0.0

    def _pick_ready_slot_locked(self, now: float) -> Optional[KeySlot]:
        self._refresh_slots_locked(now)

        for offset in range(1, self._total_keys + 1):
            slot_index = (self._round_robin_cursor + offset) % self._total_keys
            slot = self._slots[slot_index]
            if slot.status == SLOT_READY:
                self._round_robin_cursor = slot_index
                return slot
        return None

    def _next_cooldown_timeout_locked(self, now: float) -> Optional[float]:
        nearest: Optional[float] = None
        for slot in self._slots:
            if slot.status != SLOT_COOLDOWN:
                continue
            remaining = max(0.0, slot.cooldown_until - now)
            if nearest is None or remaining < nearest:
                nearest = remaining
        return nearest

    def _remove_ticket_locked(self, ticket_id: str) -> bool:
        for index, ticket in enumerate(self._wait_queue):
            if ticket.ticket_id == ticket_id:
                del self._wait_queue[index]
                return True
        return False

    def _set_slot_busy_locked(
        self,
        slot: KeySlot,
        *,
        task_type: str,
        task_id: Optional[str],
        curriculum_id: Optional[str],
    ) -> None:
        slot.status = SLOT_BUSY
        slot.current_task_type = task_type
        slot.current_task_id = task_id
        slot.cooldown_until = 0.0

        if curriculum_id:
            self._curriculum_leases[curriculum_id] = slot.slot_number

    @staticmethod
    def _matches_task(
        *,
        target_task_id: Optional[str],
        target_task_type: Optional[str],
        task_id: Optional[str],
        task_type: Optional[str],
    ) -> bool:
        if not target_task_id:
            return False
        if target_task_id != task_id:
            return False
        if target_task_type and target_task_type != task_type:
            return False
        return True

    def _release_slot_locked(self, slot: KeySlot, now: float) -> bool:
        if slot.status != SLOT_BUSY:
            return False

        slot.status = SLOT_COOLDOWN
        slot.cooldown_until = now + self._cooldown_seconds
        slot.current_task_type = None
        slot.current_task_id = None

        to_remove = [
            curriculum_id
            for curriculum_id, slot_number in self._curriculum_leases.items()
            if slot_number == slot.slot_number
        ]
        for curriculum_id in to_remove:
            self._curriculum_leases.pop(curriculum_id, None)

        return True

    async def acquire_slot(
        self,
        *,
        task_type: str,
        task_id: Optional[str] = None,
        curriculum_id: Optional[str] = None,
    ) -> int:
        """Wait for and assign one key slot.

        Queue priority is strict FIFO. Slot selection uses round-robin among
        currently ready slots.
        """

        ticket = QueueTicket(
            ticket_id=uuid.uuid4().hex,
            task_type=task_type,
            task_id=task_id,
        )

        async with self._condition:
            self._wait_queue.append(ticket)

            try:
                while True:
                    now = self._now()
                    self._refresh_slots_locked(now)

                    is_queue_head = (
                        len(self._wait_queue) > 0
                        and self._wait_queue[0].ticket_id == ticket.ticket_id
                    )

                    if is_queue_head:
                        slot = self._pick_ready_slot_locked(now)
                        if slot is not None:
                            self._wait_queue.popleft()
                            self._set_slot_busy_locked(
                                slot,
                                task_type=ticket.task_type,
                                task_id=ticket.task_id,
                                curriculum_id=curriculum_id,
                            )
                            self._condition.notify_all()
                            return slot.slot_number

                    timeout = self._next_cooldown_timeout_locked(now)
                    if timeout is None:
                        await self._condition.wait()
                        continue

                    # Wake up when cooldown may expire even without explicit notify.
                    bounded_timeout = max(timeout, 0.001)
                    try:
                        await asyncio.wait_for(
                            self._condition.wait(), timeout=bounded_timeout
                        )
                    except asyncio.TimeoutError:
                        continue
            except asyncio.CancelledError:
                if self._remove_ticket_locked(ticket.ticket_id):
                    self._condition.notify_all()
                raise
            except Exception:
                if self._remove_ticket_locked(ticket.ticket_id):
                    self._condition.notify_all()
                raise

    async def release_slot(self, slot_number: int) -> bool:
        """Release busy slot and start cooldown."""

        async with self._condition:
            slot = self._get_slot_by_number(slot_number)
            if slot is None:
                return False

            changed = self._release_slot_locked(slot, self._now())
            self._condition.notify_all()
            return changed

    async def release_curriculum_slot(self, curriculum_id: str) -> bool:
        """Release slot leased by curriculum_id (if any)."""

        async with self._condition:
            slot_number = self._curriculum_leases.pop(curriculum_id, None)
            if slot_number is None:
                return False

            slot = self._get_slot_by_number(slot_number)
            if slot is None:
                return False

            changed = self._release_slot_locked(slot, self._now())
            self._condition.notify_all()
            return changed

    async def get_snapshot(
        self,
        *,
        task_id: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> dict:
        """Return queue status snapshot for UI polling."""

        async with self._condition:
            now = self._now()
            self._refresh_slots_locked(now)

            available = 0
            busy = 0
            cooldown = 0
            slots_payload: list[dict] = []
            nearest_cooldown: Optional[float] = None

            for slot in self._slots:
                remaining = 0
                if slot.status == SLOT_READY:
                    available += 1
                elif slot.status == SLOT_BUSY:
                    busy += 1
                elif slot.status == SLOT_COOLDOWN:
                    cooldown += 1
                    remaining = max(0, math.ceil(slot.cooldown_until - now))
                    if nearest_cooldown is None or remaining < nearest_cooldown:
                        nearest_cooldown = float(remaining)

                slots_payload.append(
                    {
                        "slot_number": slot.slot_number,
                        "status": slot.status,
                        "cooldown_remaining_seconds": int(remaining),
                        "current_task_type": slot.current_task_type,
                        "current_task_id": slot.current_task_id,
                    }
                )

            waiting_jobs = len(self._wait_queue)
            my_position: Optional[int] = None
            my_status = "unknown"

            for index, ticket in enumerate(self._wait_queue):
                if self._matches_task(
                    target_task_id=task_id,
                    target_task_type=task_type,
                    task_id=ticket.task_id,
                    task_type=ticket.task_type,
                ):
                    my_position = index + 1
                    my_status = "waiting"
                    break

            if my_position is None and task_id:
                for slot in self._slots:
                    if slot.status != SLOT_BUSY:
                        continue
                    if self._matches_task(
                        target_task_id=task_id,
                        target_task_type=task_type,
                        task_id=slot.current_task_id,
                        task_type=slot.current_task_type,
                    ):
                        my_status = "processing"
                        break

            if available > 0:
                next_available_in_seconds = 0
            elif nearest_cooldown is not None:
                next_available_in_seconds = int(nearest_cooldown)
            else:
                # All slots are busy with unknown completion times.
                next_available_in_seconds = self._cooldown_seconds

            if waiting_jobs == 0:
                estimated_wait_seconds = 0
            elif available > 0:
                estimated_wait_seconds = 0
            else:
                waves = math.ceil(waiting_jobs / max(1, self._total_keys))
                estimated_wait_seconds = int(
                    next_available_in_seconds + max(0, waves - 1) * self._cooldown_seconds
                )

            return {
                "total_keys": self._total_keys,
                "cooldown_seconds": self._cooldown_seconds,
                "available_keys": available,
                "busy_keys": busy,
                "cooldown_keys": cooldown,
                "waiting_jobs": waiting_jobs,
                "estimated_wait_seconds": estimated_wait_seconds,
                "next_available_in_seconds": next_available_in_seconds,
                "my_position": my_position,
                "my_status": my_status,
                "slots": slots_payload,
            }


key_queue_service = KeyQueueService(
    total_keys=settings.KEY_QUEUE_TOTAL_KEYS,
    cooldown_seconds=settings.KEY_QUEUE_COOLDOWN_SECONDS,
)
