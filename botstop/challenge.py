from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import string
from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np

from botstop.mask import fit_text_mask
from botstop.motion import dvd_bounce_positions, orbit_positions
from botstop.noise import cutout_patch, point_static

MotionKind = Literal["bounce", "orbit"]


@dataclass(frozen=True)
class ChallengeConfig:
    width: int = 480
    height: int = 280
    font_size: int = 192
    stroke_width: int = 4
    frame_count: int = 120
    text_length: int = 4
    motion: MotionKind = "bounce"
    grain: int = 1
    charset: str = string.digits
    max_fill_ratio: float = 0.94
    min_travel_x_ratio: float = 0.05
    min_travel_y_ratio: float = 0.10


@dataclass(frozen=True)
class Challenge:
    challenge_id: str
    answer: str
    config: ChallengeConfig
    base_seed: int
    motion_seed: int
    positions: list[tuple[int, int]]
    mask: np.ndarray
    verification_token: str

    def to_public_dict(self) -> dict:
        payload = {
            "challenge_id": self.challenge_id,
            "config": asdict(self.config),
            "base_seed": self.base_seed,
            "motion_seed": self.motion_seed,
            "positions": self.positions,
            "mask_shape": list(self.mask.shape),
        }
        return payload


def random_answer(config: ChallengeConfig) -> str:
    rng = secrets.SystemRandom()
    alphabet = config.charset
    return "".join(rng.choice(alphabet) for _ in range(config.text_length))


def motion_positions(
    config: ChallengeConfig,
    mask: np.ndarray,
    motion_seed: int,
) -> list[tuple[int, int]]:
    patch_height, patch_width = mask.shape
    if config.motion == "orbit":
        return orbit_positions(
            config.frame_count,
            config.width,
            config.height,
            patch_width,
            patch_height,
            motion_seed,
        )
    return dvd_bounce_positions(
        config.frame_count,
        config.width,
        config.height,
        patch_width,
        patch_height,
        motion_seed,
    )


def make_verification_token(challenge_id: str, answer: str, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        f"{challenge_id}:{answer.upper()}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest


def generate_challenge(
    *,
    answer: str | None = None,
    config: ChallengeConfig | None = None,
    secret: str | None = None,
) -> Challenge:
    """Build a captcha challenge with deterministic render parameters."""
    config = config or ChallengeConfig()
    challenge_id = secrets.token_urlsafe(12)
    answer = (answer or random_answer(config)).upper()
    secret = secret or secrets.token_urlsafe(32)

    base_seed = secrets.randbelow(2**31 - 1)
    motion_seed = secrets.randbelow(2**31 - 1)

    mask = fit_text_mask(
        answer,
        canvas_width=config.width,
        canvas_height=config.height,
        font_size=config.font_size,
        stroke_width=config.stroke_width,
        max_fill_ratio=config.max_fill_ratio,
        min_travel_x_ratio=config.min_travel_x_ratio,
        min_travel_y_ratio=config.min_travel_y_ratio,
    )[2]
    positions = motion_positions(config, mask, motion_seed)
    token = make_verification_token(challenge_id, answer, secret)

    return Challenge(
        challenge_id=challenge_id,
        answer=answer,
        config=config,
        base_seed=base_seed,
        motion_seed=motion_seed,
        positions=positions,
        mask=mask,
        verification_token=token,
    )


def composite_frame(
    base: np.ndarray,
    patch: np.ndarray,
    mask: np.ndarray,
    x: int,
    y: int,
) -> np.ndarray:
    """Paste a static cutout onto the base at the given position."""
    canvas = base.copy()
    patch_height, patch_width = patch.shape
    canvas_height, canvas_width = canvas.shape

    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(canvas_width, x + patch_width)
    y1 = min(canvas_height, y + patch_height)

    if x0 >= x1 or y0 >= y1:
        return canvas

    patch_x0 = x0 - x
    patch_y0 = y0 - y
    patch_x1 = patch_x0 + (x1 - x0)
    patch_y1 = patch_y0 + (y1 - y0)

    region = canvas[y0:y1, x0:x1]
    patch_region = patch[patch_y0:patch_y1, patch_x0:patch_x1]
    mask_region = mask[patch_y0:patch_y1, patch_x0:patch_x1] > 127

    region[mask_region] = patch_region[mask_region]
    canvas[y0:y1, x0:x1] = region
    return canvas


def render_frames(challenge: Challenge) -> list[np.ndarray]:
    """Render every animation frame for a challenge."""
    config = challenge.config
    base = point_static(
        config.width,
        config.height,
        challenge.base_seed,
        grain=config.grain,
    )
    patch_height, patch_width = challenge.mask.shape
    patch = cutout_patch(base, patch_width, patch_height)

    frames: list[np.ndarray] = []
    for x, y in challenge.positions:
        frames.append(composite_frame(base, patch, challenge.mask, x, y))
    return frames


def serialise_challenge_bundle(challenge: Challenge, secret: str) -> str:
    """Serialise server-side verification metadata."""
    payload = {
        "challenge_id": challenge.challenge_id,
        "answer": challenge.answer,
        "token": challenge.verification_token,
        "public": challenge.to_public_dict(),
    }
    return json.dumps(payload, separators=(",", ":"))
