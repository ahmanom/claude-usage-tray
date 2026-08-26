"""QSystemTrayIcon wiring: periodic polling, tooltip, menu, and click-to-view popup."""

from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .api_client import UsageApiError, UsageSnapshot, fetch_usage
from .config import AppConfig
from .credentials import CredentialsError, load_credentials
from .detail_popup import UsageDetailPopup
from .icon_renderer import render_percent_icon


def _format_resets(resets_at: datetime | None) -> str:
    if resets_at is None:
        return "unknown"
    now = datetime.now(timezone.utc)
    delta = resets_at - now
    local_time = resets_at.astimezone().strftime("%H:%M")
    if delta.total_seconds() <= 0:
        return f"{local_time} (pending)"
    days = delta.days
    hours = delta.seconds // 3600
    if days > 0:
        return f"resets {local_time} (in {days}d {hours}h)"
    minutes = (delta.seconds % 3600) // 60
    return f"resets {local_time} (in {hours}h {minutes}m)"


def _build_tooltip(snapshot: UsageSnapshot) -> str:
    lines = ["Claude Usage Monitor"]
    if snapshot.session:
        lines.append(f"Session: {snapshot.session.percent:.0f}%  ({_format_resets(snapshot.session.resets_at)})")
    if snapshot.weekly:
        lines.append(f"Weekly:  {snapshot.weekly.percent:.0f}%  ({_format_resets(snapshot.weekly.resets_at)})")
    return "\n".join(lines)


class ClaudeUsageTrayApp:
    def __init__(self, app: QApplication, config: AppConfig):
        self._app = app
        self._config = config
        self._tray = QSystemTrayIcon()
        self._tray.setIcon(render_percent_icon(None, None, errored=False))
        self._tray.setToolTip("Claude Usage Monitor - loading...")
        self._tray.activated.connect(self._on_activated)

        self._popup = UsageDetailPopup(self._tray)

        self._menu = QMenu()
        self._status_action = QAction("Loading...")
        self._status_action.setEnabled(False)
        self._menu.addAction(self._status_action)
        self._menu.addSeparator()

        refresh_action = QAction("Refresh now")
        refresh_action.triggered.connect(self.refresh)
        self._menu.addAction(refresh_action)

        quit_action = QAction("Quit")
        quit_action.triggered.connect(self._app.quit)
        self._menu.addAction(quit_action)

        self._tray.setContextMenu(self._menu)
        self._tray.show()

        self._timer = QTimer()
        self._timer.timeout.connect(self.refresh)
        self._timer.start(self._config.poll_interval_seconds * 1000)

    def refresh(self) -> None:
        try:
            credentials = load_credentials(self._config.credentials_path)
            if credentials.is_expired:
                raise CredentialsError("Access token expired. Open Claude Code to refresh it.")
            snapshot = fetch_usage(
                access_token=credentials.access_token,
                api_url=self._config.api_url,
                anthropic_beta=self._config.anthropic_beta,
                user_agent=self._config.user_agent,
                timeout_seconds=self._config.request_timeout_seconds,
            )
        except (CredentialsError, UsageApiError) as exc:
            self._show_error(str(exc))
            return

        percent = snapshot.session.percent if snapshot.session else None
        severity = snapshot.session.severity if snapshot.session else None
        self._tray.setIcon(render_percent_icon(percent, severity))
        self._tray.setToolTip(_build_tooltip(snapshot))
        self._status_action.setText(_build_tooltip(snapshot).replace("\n", "  |  "))

        session_text = f"{snapshot.session.percent:.0f}%" if snapshot.session else "--%"
        session_meta = _format_resets(snapshot.session.resets_at) if snapshot.session else "no data"
        weekly_text = f"{snapshot.weekly.percent:.0f}%" if snapshot.weekly else "--%"
        weekly_meta = _format_resets(snapshot.weekly.resets_at) if snapshot.weekly else "no data"
        self._popup.set_content(session_text, session_meta, weekly_text, weekly_meta)

    def _show_error(self, message: str) -> None:
        self._tray.setIcon(render_percent_icon(None, None, errored=True))
        self._tray.setToolTip(f"Claude Usage Monitor - error\n{message}")
        self._status_action.setText(f"Error: {message}")
        self._popup.set_status(message)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._popup.show_near_tray()
