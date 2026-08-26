"""Generates assets/app_icon.ico: a static asterisk-mark app identity icon.

Run once (or after changing the design): python build_icon.py
Requires Pillow (build-time only, not a runtime dependency of the tray app).
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

_BACKGROUND = (32, 32, 28, 255)
_ACCENT = (217, 119, 87, 255)
_SIZES = [16, 24, 32, 48, 64, 128, 256]
_OUTPUT_PATH = Path(__file__).resolve().parent / "assets" / "app_icon.ico"


def _draw_asterisk(draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float) -> None:
    bar_half_width = radius * 0.11
    bar_length = radius * 0.9
    for i in range(6):
        angle = math.radians(i * 60)
        dx, dy = math.cos(angle), math.sin(angle)
        px, py = -dy, dx
        tip_x, tip_y = cx + dx * bar_length, cy + dy * bar_length
        points = [
            (cx + px * bar_half_width, cy + py * bar_half_width),
            (cx - px * bar_half_width, cy - py * bar_half_width),
            (tip_x - px * bar_half_width * 0.4, tip_y - py * bar_half_width * 0.4),
            (tip_x + px * bar_half_width * 0.4, tip_y + py * bar_half_width * 0.4),
        ]
        draw.polygon(points, fill=_ACCENT)


def build_base_image(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    margin = size * 0.06
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=size * 0.22,
        fill=_BACKGROUND,
    )
    _draw_asterisk(draw, size / 2, size / 2, size * 0.34)
    return image


def main() -> None:
    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    base = build_base_image(256)
    images = [base.resize((s, s), Image.LANCZOS) for s in _SIZES if s != 256]
    base.save(_OUTPUT_PATH, format="ICO", sizes=[(s, s) for s in _SIZES], append_images=images)
    print(f"Wrote {_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
