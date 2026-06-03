from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from botstop.fonts import load_default_font


def text_mask(
    text: str,
    font_size: int,
    *,
    padding: int | None = None,
    stroke_width: int | None = None,
) -> np.ndarray:
    """
    Render text to a binary mask.

    Returns uint8 array where 255 marks glyph pixels and 0 is background.
    """
    padding = padding if padding is not None else max(16, font_size // 5)
    stroke_width = stroke_width if stroke_width is not None else max(2, font_size // 32)

    font = load_default_font(font_size)
    dummy = Image.new("L", (1, 1), 0)
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
        stroke_width=stroke_width,
    )
    width = bbox[2] - bbox[0] + padding * 2
    height = bbox[3] - bbox[1] + padding * 2

    image = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(image)
    draw.text(
        (padding - bbox[0], padding - bbox[1]),
        text,
        fill=255,
        font=font,
        stroke_width=stroke_width,
        stroke_fill=255,
    )
    return np.array(image, dtype=np.uint8)


def fit_text_mask(
    text: str,
    *,
    canvas_width: int,
    canvas_height: int,
    font_size: int,
    stroke_width: int,
    max_fill_ratio: float = 0.94,
    min_travel_x_ratio: float = 0.05,
    min_travel_y_ratio: float = 0.10,
) -> tuple[int, int, np.ndarray]:
    """
    Choose the largest font that fills the canvas while leaving room to bounce.

    ``max_fill_ratio`` caps how much of the canvas width the glyph block may use.
    Travel minimums scale with canvas size so larger frames still move naturally.
    """
    min_travel_x = max(16, int(canvas_width * min_travel_x_ratio))
    min_travel_y = max(12, int(canvas_height * min_travel_y_ratio))
    max_patch_width = int(canvas_width * max_fill_ratio)
    max_patch_height = int(canvas_height * max_fill_ratio)

    size = font_size
    stroke = stroke_width
    mask = text_mask(text, size, stroke_width=stroke)

    while size > 48:
        patch_width = mask.shape[1]
        patch_height = mask.shape[0]
        travel_x = canvas_width - patch_width
        travel_y = canvas_height - patch_height
        if (
            patch_width <= max_patch_width
            and patch_height <= max_patch_height
            and travel_x >= min_travel_x
            and travel_y >= min_travel_y
        ):
            return size, stroke, mask

        size -= 4
        stroke = max(2, size // 48)
        mask = text_mask(text, size, stroke_width=stroke)

    return size, stroke, mask
