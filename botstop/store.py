from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ChallengeRecord:
    challenge_id: str
    answer: str
    token: str
    issued_at: float
    gif_path: Path
    digit_length: int
    solved: bool = False


class ChallengeStore:
    """In-memory challenge registry with TTL expiry."""

    def __init__(self, *, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = ttl_seconds
        self._records: dict[str, ChallengeRecord] = {}
        self._lock = threading.Lock()

    def put(self, record: ChallengeRecord) -> None:
        with self._lock:
            self._purge_expired_locked()
            self._records[record.challenge_id] = record

    def get(self, challenge_id: str) -> ChallengeRecord | None:
        with self._lock:
            self._purge_expired_locked()
            record = self._records.get(challenge_id)
            if record is None:
                return None
            if self._is_expired(record):
                self._delete_locked(challenge_id)
                return None
            return record

    def delete(self, challenge_id: str) -> None:
        with self._lock:
            self._delete_locked(challenge_id)

    def mark_solved(self, challenge_id: str) -> None:
        with self._lock:
            record = self._records.get(challenge_id)
            if record is not None:
                record.solved = True

    def _is_expired(self, record: ChallengeRecord) -> bool:
        return time.time() - record.issued_at > self.ttl_seconds

    def _delete_locked(self, challenge_id: str) -> None:
        record = self._records.pop(challenge_id, None)
        if record is not None and record.gif_path.is_file():
            record.gif_path.unlink(missing_ok=True)

    def _purge_expired_locked(self) -> None:
        expired = [
            challenge_id
            for challenge_id, record in self._records.items()
            if self._is_expired(record)
        ]
        for challenge_id in expired:
            self._delete_locked(challenge_id)
