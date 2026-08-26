"""Reads the OAuth access token Claude Code stores locally after login."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone


class CredentialsError(Exception):
    """Raised when the access token cannot be located or has expired."""


@dataclass(frozen=True)
class Credentials:
    access_token: str
    expires_at: datetime | None
    subscription_type: str | None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) >= self.expires_at


def _find_oauth_block(data: dict) -> dict:
    if "accessToken" in data:
        return data
    if "claudeAiOauth" in data and isinstance(data["claudeAiOauth"], dict):
        return data["claudeAiOauth"]
    for value in data.values():
        if isinstance(value, dict) and "accessToken" in value:
            return value
    raise CredentialsError("Could not find 'accessToken' in the credentials file.")


def load_credentials(path: str) -> Credentials:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as exc:
        raise CredentialsError(
            f"Credentials file not found at {path}. Log in with the Claude Code CLI first."
        ) from exc
    except json.JSONDecodeError as exc:
        raise CredentialsError(f"Credentials file at {path} is not valid JSON.") from exc

    oauth = _find_oauth_block(data)
    access_token = oauth.get("accessToken")
    if not access_token:
        raise CredentialsError("Credentials file did not contain a non-empty accessToken.")

    expires_at_ms = oauth.get("expiresAt")
    expires_at = (
        datetime.fromtimestamp(expires_at_ms / 1000, tz=timezone.utc)
        if isinstance(expires_at_ms, (int, float))
        else None
    )

    return Credentials(
        access_token=access_token,
        expires_at=expires_at,
        subscription_type=oauth.get("subscriptionType"),
    )
