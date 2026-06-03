from __future__ import annotations

import hmac
import secrets
import time
from dataclasses import dataclass

from botstop.challenge import make_verification_token


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    reason: str


def normalise_answer(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def verify_submission(
    *,
    challenge_id: str,
    expected_answer: str,
    submitted_answer: str,
    token: str,
    secret: str,
    issued_at: float,
    ttl_seconds: int = 300,
) -> VerificationResult:
    """Verify a captcha submission with constant-time token comparison."""
    now = time.time()
    if now - issued_at > ttl_seconds:
        return VerificationResult(False, "expired")

    submitted = normalise_answer(submitted_answer)
    expected = normalise_answer(expected_answer)
    expected_token = make_verification_token(challenge_id, expected, secret)

    if not hmac.compare_digest(token, expected_token):
        return VerificationResult(False, "invalid_token")

    if not secrets.compare_digest(submitted, expected):
        return VerificationResult(False, "incorrect")

    return VerificationResult(True, "ok")
