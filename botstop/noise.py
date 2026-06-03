from __future__ import annotations

import numpy as np


def point_static(
    width: int,
    height: int,
    seed: int,
    *,
    grain: int = 1,
) -> np.ndarray:
    """
    TV-style point static: coarse greyscale specks upscaled to full resolution.

    Real analog snow is not independent per-pixel salt and pepper. Receivers
    produce band-limited noise that reads as soft-edged *points* — each speck
    spans several display pixels. We model that by drawing random grey values on
    a coarse grid and nearest-neighbour upscaling.
    """
    grain = max(1, grain)
    rng = np.random.default_rng(seed)
    coarse_w = (width + grain - 1) // grain
    coarse_h = (height + grain - 1) // grain
    coarse = rng.integers(0, 256, size=(coarse_h, coarse_w), dtype=np.uint8)

    field = np.repeat(np.repeat(coarse, grain, axis=0), grain, axis=1)
    return field[:height, :width]


def cutout_patch(field: np.ndarray, width: int, height: int) -> np.ndarray:
    """Crop a top-left patch from an existing static field."""
    return field[:height, :width].copy()
