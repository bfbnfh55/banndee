@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py tests/test_system.py
) else (
  python tests/test_system.py
)
pause
