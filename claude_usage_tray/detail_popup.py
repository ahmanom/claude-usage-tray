"""Small popup shown near the tray icon on a single click: session + weekly detail."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

_STYLESHEET = """
QFrame#card {
    background: #20201C;
    border: 1px solid #3A3A34;
    border-radius: 10px;
}
QLabel { color: #F5F0E8; background: transparent; }
QLabel#title { font-weight: 600; font-size: 13px; }
QLabel#rowLabel { color: #B8B2A5; font-size: 11px; }
QLabel#rowValue { font-size: 15px; font-weight: 700; }
QLabel#rowMeta { color: #B8B2A5; font-size: 11px; }
QPushButton#close {
    background: transparent;
    border: none;
    color: #B8B2A5;
    font-size: 13px;
    padding: 0px 4px;
}
QPushButton#close:hover { color: #F5F0E8; }
"""


class UsageDetailPopup(QWidget):
    def __init__(self, tray_icon) -> None:
        super().__init__(None, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self._tray_icon = tray_icon
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(_STYLESHEET)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame(self)
        card.setObjectName("card")
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 10, 12)
        layout.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel("Claude Usage Monitor")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setObjectName("close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        self._session_value = QLabel("--%")
        self._session_value.setObjectName("rowValue")
        self._session_meta = QLabel("")
        self._session_meta.setObjectName("rowMeta")
        layout.addWidget(self._row("Session", self._session_value, self._session_meta))

        self._weekly_value = QLabel("--%")
        self._weekly_value.setObjectName("rowValue")
        self._weekly_meta = QLabel("")
        self._weekly_meta.setObjectName("rowMeta")
        layout.addWidget(self._row("Weekly", self._weekly_value, self._weekly_meta))

        self.setFixedWidth(220)

    def _row(self, label_text: str, value_label: QLabel, meta_label: QLabel) -> QWidget:
        row = QWidget()
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        top = QHBoxLayout()
        label = QLabel(label_text)
        label.setObjectName("rowLabel")
        top.addWidget(label)
        top.addStretch()
        top.addWidget(value_label)
        row_layout.addLayout(top)
        row_layout.addWidget(meta_label)
        return row

    def set_status(self, text: str) -> None:
        self._session_value.setText("--%")
        self._weekly_value.setText("--%")
        self._session_meta.setText(text)
        self._weekly_meta.setText("")

    def set_content(self, session_text: str, session_meta: str, weekly_text: str, weekly_meta: str) -> None:
        self._session_value.setText(session_text)
        self._session_meta.setText(session_meta)
        self._weekly_value.setText(weekly_text)
        self._weekly_meta.setText(weekly_meta)

    def show_near_tray(self) -> None:
        self.adjustSize()
        anchor = self._anchor_point()
        screen = QGuiApplication.screenAt(anchor) or QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()

        x = anchor.x() - self.width() // 2
        x = max(avail.left() + 4, min(x, avail.right() - self.width() - 4))
        y = avail.bottom() - self.height() - 4

        self.move(x, y)
        self.show()
        self.activateWindow()
        self.raise_()

    def _anchor_point(self) -> QPoint:
        geometry = self._tray_icon.geometry()
        if geometry.isValid() and geometry.width() > 0:
            return geometry.center()
        screen = QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()
        return QPoint(avail.right() - 20, avail.bottom())
