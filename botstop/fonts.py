from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import ImageFont


def load_default_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Pick a readable system font, falling back to Pillow's bitmap default."""
    candidates: list[Path | str] = []

    if sys.platform == "win32":
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        candidates.extend(
            [
                windir / "Fonts" / "arial.ttf",
                windir / "Fonts" / "segoeui.ttf",
                windir / "Fonts" / "arialbd.ttf",
                windir / "Fonts" / "segoeuib.ttf",
            ]
        )
    elif sys.platform == "darwin":
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            ]
        )

    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return ImageFont.truetype(str(path), size=size)

    return ImageFont.load_default()
