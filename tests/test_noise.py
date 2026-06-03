from __future__ import annotations

import numpy as np

from botstop.noise import point_static


def test_point_static_uses_coarse_grain_blocks():
    field = point_static(64, 64, seed=7, grain=4)
    assert field.shape == (64, 64)
    assert field.dtype == np.uint8
    # Each 4x4 block shares one sampled value.
    assert field[0, 0] == field[3, 3]
    assert field[4, 0] == field[7, 3]
    assert len(np.unique(field)) > 8


def test_point_static_grain_one_is_per_pixel():
    field = point_static(16, 16, seed=1, grain=1)
    assert field.shape == (16, 16)
