from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from botstop.challenge import (
    Challenge,
    ChallengeConfig,
    generate_challenge,
    serialise_challenge_bundle,
)
from botstop.render import render_gif, render_preview_html
from botstop.verify import VerificationResult, verify_submission


def default_secret() -> str:
    return os.environ.get("BOTSTOP_SECRET", "local-dev-secret")


@dataclass(frozen=True)
class CaptchaArtifacts:
    """Files and metadata produced by :func:`create_captcha`."""

    challenge: Challenge
    gif_path: Path
    html_path: Path
    metadata_path: Path
    bundle_path: Path | None = None


def create_captcha(
    *,
    answer: str | None = None,
    config: ChallengeConfig | None = None,
    output_dir: Path | str = "outputs",
    secret: str | None = None,
    fps: float = 12.0,
    write_bundle: bool = True,
    demo_html: bool = True,
) -> CaptchaArtifacts:
    """
    Generate a captcha challenge and write GIF/HTML artefacts to disk.

    The answer is random unless ``answer`` is supplied (testing only).
    By default the HTML demo embeds a local answer check; set ``demo_html=False``
    for production pages that verify server-side only.

    Example::

        from botstop import create_captcha

        result = create_captcha(output_dir="outputs")
        # verify with result.bundle_path on your server
    """
    config = config or ChallengeConfig()
    secret = secret or default_secret()
    challenge = generate_challenge(answer=answer, config=config, secret=secret)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = out / challenge.challenge_id

    gif_path = render_gif(challenge, stem.with_suffix(".gif"), fps=fps)
    html_path = render_preview_html(
        challenge,
        stem.with_suffix(".html"),
        fps=fps,
        gif_path=gif_path,
        demo=demo_html,
    )

    metadata = {
        "challenge_id": challenge.challenge_id,
        "gif": str(gif_path),
        "html": str(html_path),
        "frame_count": config.frame_count,
        "motion": config.motion,
    }
    metadata_path = stem.with_suffix(".json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    bundle_path: Path | None = None
    if write_bundle:
        bundle_path = stem.with_suffix(".bundle.json")
        bundle_path.write_text(
            serialise_challenge_bundle(challenge, secret),
            encoding="utf-8",
        )

    return CaptchaArtifacts(
        challenge=challenge,
        gif_path=gif_path,
        html_path=html_path,
        metadata_path=metadata_path,
        bundle_path=bundle_path,
    )


def verify_captcha(
    *,
    bundle_path: Path | str,
    submitted_answer: str,
    secret: str | None = None,
    ttl_seconds: int = 300,
) -> VerificationResult:
    """Verify a user answer against a server-side bundle file."""
    path = Path(bundle_path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    return verify_submission(
        challenge_id=bundle["challenge_id"],
        expected_answer=bundle["answer"],
        submitted_answer=submitted_answer,
        token=bundle["token"],
        secret=secret or default_secret(),
        issued_at=path.stat().st_mtime,
        ttl_seconds=ttl_seconds,
    )
