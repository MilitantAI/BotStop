from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from botstop.api import create_captcha
from botstop.challenge import ChallengeConfig
from botstop.store import ChallengeRecord, ChallengeStore
from botstop.verify import VerificationResult, verify_submission


@dataclass(frozen=True)
class PublicChallenge:
    challenge_id: str
    gif_url: str
    digit_length: int
    expires_in: int


class ChallengeService:
    def __init__(
        self,
        *,
        store: ChallengeStore,
        storage_dir: Path,
        secret: str,
        ttl_seconds: int,
        config: ChallengeConfig | None = None,
    ) -> None:
        self.store = store
        self.storage_dir = storage_dir
        self.secret = secret
        self.ttl_seconds = ttl_seconds
        self.config = config or ChallengeConfig()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def create(self, *, answer: str | None = None) -> PublicChallenge:
        result = create_captcha(
            answer=answer,
            config=self.config,
            output_dir=self.storage_dir,
            secret=self.secret,
            write_bundle=False,
            demo_html=False,
        )
        issued_at = time.time()
        record = ChallengeRecord(
            challenge_id=result.challenge.challenge_id,
            answer=result.challenge.answer,
            token=result.challenge.verification_token,
            issued_at=issued_at,
            gif_path=result.gif_path,
            digit_length=self.config.text_length,
        )
        self.store.put(record)
        return PublicChallenge(
            challenge_id=record.challenge_id,
            gif_url=f"/v1/challenges/{record.challenge_id}/animation.gif",
            digit_length=record.digit_length,
            expires_in=self.ttl_seconds,
        )

    def refresh(self, previous_id: str | None = None) -> PublicChallenge:
        if previous_id:
            self.store.delete(previous_id)
        return self.create()

    def verify(self, challenge_id: str, submitted_answer: str) -> VerificationResult:
        record = self.store.get(challenge_id)
        if record is None:
            return VerificationResult(False, "not_found")
        if record.solved:
            return VerificationResult(False, "already_solved")

        result = verify_submission(
            challenge_id=record.challenge_id,
            expected_answer=record.answer,
            submitted_answer=submitted_answer,
            token=record.token,
            secret=self.secret,
            issued_at=record.issued_at,
            ttl_seconds=self.ttl_seconds,
        )
        if result.ok:
            self.store.mark_solved(challenge_id)
        return result

    def gif_path(self, challenge_id: str) -> Path | None:
        record = self.store.get(challenge_id)
        if record is None:
            return None
        return record.gif_path
