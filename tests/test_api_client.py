import io
from unittest.mock import patch

import pytest

from claude_usage_tray.api_client import RateLimitedError, UsageApiError, fetch_usage, parse_usage_response

_SAMPLE_RESPONSE = {
    "five_hour": {"utilization": 57.0, "resets_at": "2026-08-27T11:30:00.859514+00:00"},
    "seven_day": {"utilization": 21.0, "resets_at": "2026-09-02T00:00:00.859540+00:00"},
    "limits": [
        {
            "kind": "session",
            "group": "session",
            "percent": 57,
            "severity": "normal",
            "resets_at": "2026-08-27T11:30:00.859514+00:00",
            "scope": None,
            "is_active": True,
        },
        {
            "kind": "weekly_all",
            "group": "weekly",
            "percent": 21,
            "severity": "normal",
            "resets_at": "2026-09-02T00:00:00.859540+00:00",
            "scope": None,
            "is_active": False,
        },
    ],
}


def test_parses_session_and_weekly_limits():
    snapshot = parse_usage_response(_SAMPLE_RESPONSE)
    assert snapshot.session is not None
    assert snapshot.session.percent == 57.0
    assert snapshot.session.severity == "normal"
    assert snapshot.session.resets_at is not None

    assert snapshot.weekly is not None
    assert snapshot.weekly.percent == 21.0
    assert snapshot.weekly.is_active is False


def test_missing_limits_returns_none_windows():
    snapshot = parse_usage_response({"limits": []})
    assert snapshot.session is None
    assert snapshot.weekly is None


def test_high_severity_parsed():
    data = {
        "limits": [
            {
                "kind": "session",
                "percent": 96,
                "severity": "critical",
                "resets_at": None,
                "is_active": True,
            }
        ]
    }
    snapshot = parse_usage_response(data)
    assert snapshot.session.severity == "critical"
    assert snapshot.session.resets_at is None


def test_fetch_usage_raises_rate_limited_error_on_429():
    import urllib.error

    http_error = urllib.error.HTTPError(
        url="https://example.invalid/usage",
        code=429,
        msg="Too Many Requests",
        hdrs=None,
        fp=io.BytesIO(b""),
    )
    with patch("claude_usage_tray.api_client.urllib.request.urlopen", side_effect=http_error):
        with pytest.raises(RateLimitedError):
            fetch_usage(
                access_token="test-token",
                api_url="https://example.invalid/usage",
                anthropic_beta="test-beta",
                user_agent="test-agent",
                timeout_seconds=5,
            )


def test_fetch_usage_raises_generic_error_on_other_http_status():
    import urllib.error

    http_error = urllib.error.HTTPError(
        url="https://example.invalid/usage",
        code=500,
        msg="Server Error",
        hdrs=None,
        fp=io.BytesIO(b""),
    )
    with patch("claude_usage_tray.api_client.urllib.request.urlopen", side_effect=http_error):
        with pytest.raises(UsageApiError) as exc_info:
            fetch_usage(
                access_token="test-token",
                api_url="https://example.invalid/usage",
                anthropic_beta="test-beta",
                user_agent="test-agent",
                timeout_seconds=5,
            )
    assert not isinstance(exc_info.value, RateLimitedError)
