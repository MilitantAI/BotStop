from __future__ import annotations

from botstop.challenge import ChallengeConfig, generate_challenge
from botstop.mask import fit_text_mask


def test_fit_text_mask_maximises_fill():
    config = ChallengeConfig()
    font_size, stroke, mask = fit_text_mask(
        "1129",
        canvas_width=config.width,
        canvas_height=config.height,
        font_size=config.font_size,
        stroke_width=config.stroke_width,
        max_fill_ratio=config.max_fill_ratio,
        min_travel_x_ratio=config.min_travel_x_ratio,
        min_travel_y_ratio=config.min_travel_y_ratio,
    )
    fill = mask.shape[1] / config.width
    assert font_size >= 168
    assert fill >= 0.88
    assert config.width - mask.shape[1] >= int(config.width * config.min_travel_x_ratio)


def test_generate_challenge_has_motion_room():
    challenge = generate_challenge(answer="1129")
    positions = set(challenge.positions)
    assert len(positions) > 8
    xs = [x for x, _ in positions]
    ys = [y for _, y in positions]
    assert max(xs) - min(xs) >= 20
    assert max(ys) - min(ys) >= 30
