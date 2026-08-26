"""Client for Anthropic's OAuth usage endpoint (the same one /usage uses)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


class UsageApiError(Exception):
    """Raised when the usage endpoint cannot be reached or returns an error."""


@dataclass(frozen=True)
class LimitWindow:
    percent: float
    severity: str
    resets_at: Optional[datetime]
    is_active: bool


@dataclass(frozen=True)
class UsageSnapshot:
    session: Optional[LimitWindow]
    weekly: Optional[LimitWindow]
    raw: dict


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _limit_window(limits: list[dict], kind: str) -> Optional[LimitWindow]:
    for entry in limits:
        if entry.get("kind") == kind:
            return LimitWindow(
                percent=float(entry.get("percent", 0.0)),
                severity=entry.get("severity", "normal"),
                resets_at=_parse_datetime(entry.get("resets_at")),
                is_active=bool(entry.get("is_active", False)),
            )
    return None


def parse_usage_response(data: dict) -> UsageSnapshot:
    limits = data.get("limits", []) or []
    return UsageSnapshot(
        session=_limit_window(limits, "session"),
        weekly=_limit_window(limits, "weekly_all"),
        raw=data,
    )


def fetch_usage(
    access_token: str,
    api_url: str,
    anthropic_beta: str,
    user_agent: str,
    timeout_seconds: int,
) -> UsageSnapshot:
    request = urllib.request.Request(
        api_url,
        method="GET",
        headers={
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Anthropic-Beta": anthropic_beta,
            "User-Agent": user_agent,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise UsageApiError(
                f"Authentication rejected (HTTP {exc.code}). "
                "The access token may be expired; open Claude Code to refresh it."
            ) from exc
        raise UsageApiError(f"Usage API returned HTTP {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise UsageApiError(f"Could not reach usage API: {exc.reason}") from exc

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise UsageApiError("Usage API returned invalid JSON.") from exc

    return parse_usage_response(data)
