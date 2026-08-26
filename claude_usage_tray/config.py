"""Runtime configuration for the Claude Usage Monitor tray app."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass

DEFAULT_CREDENTIALS_PATH = os.path.expandvars(r"%USERPROFILE%\.claude\.credentials.json")
DEFAULT_API_URL = "https://api.anthropic.com/api/oauth/usage"
DEFAULT_ANTHROPIC_BETA = "oauth-2025-04-20"
DEFAULT_USER_AGENT = "claude-usage-tray/0.1.0 (python; personal-use)"
DEFAULT_POLL_INTERVAL_SECONDS = 120
REQUEST_TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class AppConfig:
    credentials_path: str
    api_url: str
    anthropic_beta: str
    user_agent: str
    poll_interval_seconds: int
    request_timeout_seconds: int


def parse_args(argv: list[str] | None = None) -> AppConfig:
    parser = argparse.ArgumentParser(
        description="Show Claude Code session/weekly usage percentage in the Windows tray."
    )
    parser.add_argument(
        "--credentials-path",
        default=DEFAULT_CREDENTIALS_PATH,
        help="Path to Claude Code's .credentials.json (default: %(default)s)",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help="Usage API endpoint (default: %(default)s)",
    )
    parser.add_argument(
        "--beta-header",
        default=DEFAULT_ANTHROPIC_BETA,
        help="Value for the Anthropic-Beta request header (default: %(default)s)",
    )
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help="User-Agent header sent with usage requests (default: %(default)s)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Polling interval in seconds (default: %(default)s)",
    )
    args = parser.parse_args(argv)
    return AppConfig(
        credentials_path=args.credentials_path,
        api_url=args.api_url,
        anthropic_beta=args.beta_header,
        user_agent=args.user_agent,
        poll_interval_seconds=args.interval,
        request_timeout_seconds=REQUEST_TIMEOUT_SECONDS,
    )
