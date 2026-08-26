@echo off
setlocal
set SCRIPT_DIR=%~dp0
if exist "%SCRIPT_DIR%.venv\Scripts\pythonw.exe" (
    set PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\pythonw.exe
) else (
    set PYTHON_EXE=pythonw
)
cd /d "%SCRIPT_DIR%"
start "" "%PYTHON_EXE%" -m claude_usage_tray.main %*
endlocal
