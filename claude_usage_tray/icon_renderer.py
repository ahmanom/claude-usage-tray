"""Renders the live tray icon: a colored badge with the usage percentage."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPixmap

_SEVERITY_COLORS = {
    "normal": QColor("#4CAF7D"),
    "warning": QColor("#E0A83E"),
    "critical": QColor("#D9534F"),
}
_BACKGROUND = QColor("#20201C")
_ACCENT = QColor("#D97757")
_TEXT_COLOR = QColor("#F5F0E8")
_ICON_SIZE = 32


def _severity_color(severity: str | None) -> QColor:
    return _SEVERITY_COLORS.get(severity or "normal", _SEVERITY_COLORS["normal"])


def _draw_asterisk(painter: QPainter, center: QPointF, radius: float, color: QColor) -> None:
    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.translate(center)
    for i in range(6):
        painter.save()
        painter.rotate(i * 60)
        bar = QRectF(-radius * 0.09, -radius, radius * 0.18, radius * 0.42)
        path = QPainterPath()
        path.addRoundedRect(bar, bar.width() / 2, bar.width() / 2)
        painter.drawPath(path)
        painter.restore()
    painter.restore()


def render_percent_icon(percent: float | None, severity: str | None, errored: bool = False) -> QIcon:
    """Draws a small square badge showing the usage percentage, color-coded by severity."""
    pixmap = QPixmap(_ICON_SIZE, _ICON_SIZE)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    rect = QRectF(1, 1, _ICON_SIZE - 2, _ICON_SIZE - 2)
    path = QPainterPath()
    path.addRoundedRect(rect, 8, 8)
    painter.fillPath(path, _BACKGROUND)

    if errored or percent is None:
        painter.setPen(_SEVERITY_COLORS["critical"])
        font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "!")
        painter.end()
        return QIcon(pixmap)

    # Small asterisk accent, top-right corner, subtle.
    accent_center = QPointF(_ICON_SIZE - 8, 8)
    _draw_asterisk(painter, accent_center, 5.0, _ACCENT)

    color = _severity_color(severity)
    ring_rect = rect.adjusted(2, 2, -2, -2)
    pen = painter.pen()
    pen.setColor(color)
    pen.setWidthF(2.4)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(ring_rect, 90 * 16, -int(min(percent, 100.0) / 100.0 * 360 * 16))

    painter.setPen(_TEXT_COLOR)
    label = str(int(round(percent)))
    font_size = 15 if len(label) <= 2 else 12
    font = QFont("Segoe UI", font_size, QFont.Weight.Bold)
    painter.setFont(font)
    text_rect = rect.adjusted(0, 3, 0, 0)
    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, label)

    painter.end()
    return QIcon(pixmap)
