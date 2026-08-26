"""Entry point: launches the Claude Usage Monitor tray app."""

from __future__ import annotations

import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .config import parse_args
from .single_instance import acquire_lock, release_lock
from .tray_app import ClaudeUsageTrayApp

_ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "app_icon.ico"
_CRASH_LOG_PATH = Path(tempfile.gettempdir()) / "claude-usage-monitor-crash.log"


def _run() -> int:
    config = parse_args()

    if not acquire_lock():
        return 0  # Another instance is already running.

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Claude Usage Monitor")
    app.aboutToQuit.connect(release_lock)
    if _ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(_ICON_PATH)))

    tray_app = ClaudeUsageTrayApp(app, config)
    tray_app.refresh()

    return app.exec()


def main() -> int:
    try:
        return _run()
    except Exception:
        with open(_CRASH_LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(f"\n--- {datetime.now().isoformat()} ---\n")
            traceback.print_exc(file=log_file)
        raise


if __name__ == "__main__":
    sys.exit(main())
