"""Entry point: launches the Claude Usage Monitor tray app."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .config import parse_args
from .tray_app import ClaudeUsageTrayApp

_ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "app_icon.ico"


def main() -> int:
    config = parse_args()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Claude Usage Monitor")
    if _ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(_ICON_PATH)))

    tray_app = ClaudeUsageTrayApp(app, config)
    tray_app.refresh()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
