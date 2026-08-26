"""QSystemTrayIcon wiring: periodic polling, menu, and click-to-view popup.

No native hover tooltip is used for usage detail (Windows renders multi-line
tray tooltips as a cramped single line) - detail lives only in the popup
(single click / Open) and the tray icon's own color-coded percentage.
"""

from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .api_client import UsageApiError, fetch_usage
from .config import AppConfig
from .credentials import CredentialsError, load_credentials
from .detail_popup import UsageDetailPopup
from .icon_renderer import render_percent_icon

_APP_TOOLTIP = "Claude Usage Monitor"


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


def build_tray_menu(on_open, on_refresh, on_close) -> QMenu:
    """Builds the tray context menu.

    Actions are created via QMenu.addAction(str) so the menu owns them. Creating
    QAction objects separately and passing them to addAction() does not transfer
    ownership in PySide6, so they would be garbage collected right after this
    function returns and the menu would silently render empty on right-click.
    """
    menu = QMenu()
    menu.addAction("Open").triggered.connect(on_open)
    menu.addAction("Refresh now").triggered.connect(on_refresh)
    menu.addSeparator()
    menu.addAction("Close").triggered.connect(on_close)
    return menu


class ClaudeUsageTrayApp:
    def __init__(self, app: QApplication, config: AppConfig):
        self._app = app
        self._config = config
        self._tray = QSystemTrayIcon()
        self._tray.setIcon(render_percent_icon(None, None, errored=False))
        self._tray.setToolTip(_APP_TOOLTIP)
        self._tray.activated.connect(self._on_activated)

        self._popup = UsageDetailPopup(self._tray)

        self._menu = build_tray_menu(self._show_popup, self.refresh, self._app.quit)
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

        session_text = f"{snapshot.session.percent:.0f}%" if snapshot.session else "--%"
        session_meta = _format_resets(snapshot.session.resets_at) if snapshot.session else "no data"
        weekly_text = f"{snapshot.weekly.percent:.0f}%" if snapshot.weekly else "--%"
        weekly_meta = _format_resets(snapshot.weekly.resets_at) if snapshot.weekly else "no data"
        self._popup.set_content(session_text, session_meta, weekly_text, weekly_meta)

    def _show_error(self, message: str) -> None:
        self._tray.setIcon(render_percent_icon(None, None, errored=True))
        self._popup.set_status(message)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_popup()

    def _show_popup(self) -> None:
        self._popup.show_near_tray()
