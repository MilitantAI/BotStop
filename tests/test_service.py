from __future__ import annotations

from pathlib import Path

from botstop.challenge import ChallengeConfig
from botstop.service import ChallengeService
from botstop.settings import Settings
from botstop.store import ChallengeStore


def test_service_verify_marks_solved(tmp_path: Path) -> None:
    settings = Settings(
        secret="test-secret",
        storage_dir=tmp_path,
        ttl_seconds=300,
        host="127.0.0.1",
        port=8787,
        cors_origins=["*"],
        rate_limit_per_minute=1000,
        api_key=None,
    )
    store = ChallengeStore(ttl_seconds=settings.ttl_seconds)
    service = ChallengeService(
        store=store,
        storage_dir=settings.storage_dir,
        secret=settings.secret,
        ttl_seconds=settings.ttl_seconds,
        config=ChallengeConfig(text_length=4, frame_count=12),
    )

    created = service.create(answer="1234")
    record = store.get(created.challenge_id)
    assert record is not None

    ok = service.verify(created.challenge_id, "1234")
    assert ok.ok

    again = service.verify(created.challenge_id, "1234")
    assert again.ok is False
    assert again.reason == "already_solved"
