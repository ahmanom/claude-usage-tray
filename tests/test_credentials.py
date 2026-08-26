import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from claude_usage_tray.credentials import CredentialsError, load_credentials


def _write_creds(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / ".credentials.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_loads_nested_claude_ai_oauth_structure(tmp_path: Path):
    future_ms = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp() * 1000)
    path = _write_creds(
        tmp_path,
        {
            "claudeAiOauth": {
                "accessToken": "sk-ant-oat01-fake-synthetic-token",
                "expiresAt": future_ms,
                "subscriptionType": "pro",
            }
        },
    )
    creds = load_credentials(str(path))
    assert creds.access_token == "sk-ant-oat01-fake-synthetic-token"
    assert creds.subscription_type == "pro"
    assert creds.is_expired is False


def test_loads_flat_structure(tmp_path: Path):
    path = _write_creds(tmp_path, {"accessToken": "sk-ant-oat01-fake-flat-token"})
    creds = load_credentials(str(path))
    assert creds.access_token == "sk-ant-oat01-fake-flat-token"


def test_expired_token_detected(tmp_path: Path):
    past_ms = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp() * 1000)
    path = _write_creds(
        tmp_path,
        {"claudeAiOauth": {"accessToken": "sk-ant-oat01-fake-expired", "expiresAt": past_ms}},
    )
    creds = load_credentials(str(path))
    assert creds.is_expired is True


def test_missing_file_raises(tmp_path: Path):
    with pytest.raises(CredentialsError):
        load_credentials(str(tmp_path / "does-not-exist.json"))


def test_missing_access_token_raises(tmp_path: Path):
    path = _write_creds(tmp_path, {"claudeAiOauth": {"subscriptionType": "pro"}})
    with pytest.raises(CredentialsError):
        load_credentials(str(path))
