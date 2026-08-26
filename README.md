# Claude Usage Monitor

Windows system-tray app that shows your current Claude Code session usage
percentage (from the same endpoint the `/usage` command uses), with a
richer session + weekly view in the tray tooltip and context menu.

## How it works

Claude Code stores an OAuth access token locally after login, at
`%USERPROFILE%\.claude\.credentials.json`. This app reads that token and
calls `GET https://api.anthropic.com/api/oauth/usage` (an undocumented
endpoint reverse-engineered by inspecting Claude Code's own traffic), then
renders the returned session/weekly percentages as a tray icon.

Because this endpoint is undocumented, Anthropic can change or remove it
without notice. If usage stops updating, check for an HTTP error in the
tray tooltip first.

## Setup

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
python build_icon.py
```

## Run

```
run_claude_usage_tray.bat
```

or directly:

```
.venv\Scripts\python -m claude_usage_tray.main
```

Useful flags: `--interval SECONDS` (default 120), `--credentials-path PATH`,
`--beta-header VALUE`, `--user-agent VALUE`, `--api-url URL`.

## Limitations

- The access token is only refreshed by the `claude` CLI itself. If it
  expires and you haven't used Claude Code in a while, this app will show
  an error state until you run `claude` again to refresh it. It does not
  perform its own OAuth token refresh.
- Only the top-level `session` and `weekly_all` limit windows are shown;
  the API response includes several other fields that are currently null
  for most accounts (e.g. per-model weekly limits, extra usage credits).

## Tests

```
.venv\Scripts\pytest
```

Tests use synthetic fixture data only, never real credentials.

## Packaging (optional)

```
.venv\Scripts\pyinstaller --windowed --onefile --icon assets\app_icon.ico ^
    --name "Claude Usage Monitor" claude_usage_tray\main.py
```

This produces `dist\Claude Usage Monitor.exe`. Creating a Start Menu
shortcut for it requires writing to a user-level Windows location outside
this project directory — ask if you'd like the exact shortcut-creation
command for that.
