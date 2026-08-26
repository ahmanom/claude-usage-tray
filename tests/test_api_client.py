from claude_usage_tray.api_client import parse_usage_response

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
