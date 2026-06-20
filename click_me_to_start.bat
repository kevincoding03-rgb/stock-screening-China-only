@echo off
REM ============================================================
REM  DZH - A-Share Stock Screener Launcher
REM  Pure ASCII bat: delegates all UI / language / deps to PS1
REM ============================================================

set "SCRIPT_DIR=%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%start.ps1"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Launcher exited with code %errorlevel%
)

pause
exit /b %errorlevel%
