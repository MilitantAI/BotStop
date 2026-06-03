"""BotStop: captcha text hidden in moving greyscale static."""

from botstop.api import CaptchaArtifacts, create_captcha, verify_captcha
from botstop.challenge import (
    Challenge,
    ChallengeConfig,
    generate_challenge,
    render_frames,
)
from botstop.render import render_gif, render_preview_html
from botstop.verify import VerificationResult, verify_submission

__all__ = [
    "CaptchaArtifacts",
    "Challenge",
    "ChallengeConfig",
    "VerificationResult",
    "create_captcha",
    "generate_challenge",
    "render_frames",
    "render_gif",
    "render_preview_html",
    "verify_captcha",
    "verify_submission",
    "__version__",
]

__version__ = "0.3.0"
