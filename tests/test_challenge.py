from __future__ import annotations

from pathlib import Path

import time

import numpy as np

from botstop.challenge import (
    ChallengeConfig,
    composite_frame,
    generate_challenge,
    make_verification_token,
    render_frames,
)
from botstop.mask import text_mask
from botstop.verify import verify_submission


def test_text_mask_marks_glyph_pixels():
    mask = text_mask("AB", font_size=32)
    assert mask.shape[0] > 0 and mask.shape[1] > 0
    assert mask.max() == 255
    assert mask.min() == 0
    assert mask.sum() > 0


def test_composite_only_changes_masked_pixels():
    base = np.full((40, 60), 100, dtype=np.uint8)
    patch = np.full((10, 20), 200, dtype=np.uint8)
    mask = np.zeros((10, 20), dtype=np.uint8)
    mask[2:8, 5:15] = 255

    frame = composite_frame(base, patch, mask, x=10, y=5)
    assert frame[5, 10] == 100
    assert frame[7, 20] == 200
    assert frame[0, 0] == 100


def test_render_frames_count_matches_positions():
    challenge = generate_challenge(answer="HELLO", config=ChallengeConfig(frame_count=12))
    frames = render_frames(challenge)
    assert len(frames) == len(challenge.positions)
    assert frames[0].shape == (challenge.config.height, challenge.config.width)


def test_dvd_bounce_covers_screen():
    from botstop.motion import dvd_bounce_positions

    positions = dvd_bounce_positions(120, 480, 240, 120, 60, seed=9)
    assert len(positions) == 120
    assert len(set(positions)) > 20
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    assert min(xs) <= 4
    assert max(xs) >= 100
    assert min(ys) <= 4
    assert max(ys) >= 40


def test_positions_change_over_time():
    challenge = generate_challenge(answer="MOVE", config=ChallengeConfig(frame_count=24))
    assert len(set(challenge.positions)) > 1


def test_moving_cutout_misaligns_from_base():
    from botstop.noise import point_static

    mask = text_mask("AB", font_size=32)
    base = point_static(200, 100, seed=42, grain=4)
    patch_height, patch_width = mask.shape
    patch = base[:patch_height, :patch_width].copy()

    at_origin = composite_frame(base, patch, mask, x=0, y=0)
    assert np.array_equal(
        at_origin[:patch_height, :patch_width][mask > 127],
        base[:patch_height, :patch_width][mask > 127],
    )

    moved = composite_frame(base, patch, mask, x=24, y=12)
    y0, x0 = 12, 24
    assert not np.array_equal(
        moved[y0 : y0 + patch_height, x0 : x0 + patch_width][mask > 127],
        base[y0 : y0 + patch_height, x0 : x0 + patch_width][mask > 127],
    )


def test_random_answer_uses_digits_only():
    answers = {generate_challenge().answer for _ in range(24)}
    assert all(value.isdigit() for value in answers)
    assert all(len(value) == ChallengeConfig.text_length for value in answers)
    assert len(answers) > 1


def test_html_demo_includes_answer_check(tmp_path: Path):
    from botstop import create_captcha

    result = create_captcha(answer="SECRET", output_dir=tmp_path, write_bundle=False, demo_html=True)
    html = result.html_path.read_text(encoding="utf-8")
    assert "Check answer" in html
    assert "SECRET" in html


def test_html_production_omits_answer(tmp_path: Path):
    from botstop import create_captcha

    result = create_captcha(answer="SECRET", output_dir=tmp_path, write_bundle=False, demo_html=False)
    html = result.html_path.read_text(encoding="utf-8")
    assert "SECRET" not in html
    assert "Check answer" not in html


def test_verification_round_trip():
    challenge = generate_challenge(answer="482913", secret="test-secret")
    token = make_verification_token(challenge.challenge_id, challenge.answer, "test-secret")
    result = verify_submission(
        challenge_id=challenge.challenge_id,
        expected_answer=challenge.answer,
        submitted_answer="482 913",
        token=token,
        secret="test-secret",
        issued_at=time.time(),
        ttl_seconds=10_000,
    )
    assert result.ok

    wrong = verify_submission(
        challenge_id=challenge.challenge_id,
        expected_answer=challenge.answer,
        submitted_answer="000000",
        token=token,
        secret="test-secret",
        issued_at=time.time(),
        ttl_seconds=10_000,
    )
    assert not wrong.ok
