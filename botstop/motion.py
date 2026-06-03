from __future__ import annotations

import math

import numpy as np


def _step_dvd_bounce(
    x: float,
    y: float,
    vx: float,
    vy: float,
    max_x: int,
    max_y: int,
) -> tuple[float, float, float, float]:
    x += vx
    y += vy

    if x <= 0:
        x = 0.0
        vx = abs(vx)
    elif x >= max_x:
        x = float(max_x)
        vx = -abs(vx)

    if y <= 0:
        y = 0.0
        vy = abs(vy)
    elif y >= max_y:
        y = float(max_y)
        vy = -abs(vy)

    return x, y, vx, vy


def dvd_bounce_positions(
    frame_count: int,
    canvas_width: int,
    canvas_height: int,
    patch_width: int,
    patch_height: int,
    seed: int,
) -> list[tuple[int, int]]:
    """
    DVD-screensaver bounce: constant velocity, reflects off each wall.

    Keeps travelling across the full screen rather than shuttling between
    two points.
    """
    rng = np.random.default_rng(seed)
    max_x = max(0, canvas_width - patch_width)
    max_y = max(0, canvas_height - patch_height)

    speeds: list[int]
    if max_x <= 0 or max_y <= 0:
        speeds = [1]
    else:
        travel = min(max_x, max_y)
        if travel < 40:
            speeds = [1, 1, 2]
        elif travel < 100:
            speeds = [1, 2, 3]
        else:
            speeds = [2, 3, 4]
    x = float(rng.integers(0, max(max_x, 1) + 1))
    y = float(rng.integers(0, max(max_y, 1) + 1))
    vx = float(rng.choice(speeds)) * float(rng.choice([-1, 1]))
    vy = float(rng.choice(speeds)) * float(rng.choice([-1, 1]))

    positions: list[tuple[int, int]] = []
    for _ in range(frame_count):
        positions.append((int(round(x)), int(round(y))))
        x, y, vx, vy = _step_dvd_bounce(x, y, vx, vy, max_x, max_y)

    return positions


def orbit_positions(
    frame_count: int,
    canvas_width: int,
    canvas_height: int,
    patch_width: int,
    patch_height: int,
    seed: int,
) -> list[tuple[int, int]]:
    """Move a patch on a slightly irregular orbit."""
    rng = np.random.default_rng(seed)
    max_x = max(0, canvas_width - patch_width)
    max_y = max(0, canvas_height - patch_height)
    centre_x = max_x / 2.0
    centre_y = max_y / 2.0
    radius_x = max(8.0, centre_x * float(rng.uniform(0.55, 0.85)))
    radius_y = max(6.0, centre_y * float(rng.uniform(0.45, 0.75)))

    positions: list[tuple[int, int]] = []
    for frame in range(frame_count):
        t = math.tau * frame / frame_count
        x = centre_x + math.cos(t) * radius_x
        y = centre_y + math.sin(t * 1.37) * radius_y
        positions.append(
            (
                int(round(min(max(x, 0.0), max_x))),
                int(round(min(max(y, 0.0), max_y))),
            )
        )
    return positions
