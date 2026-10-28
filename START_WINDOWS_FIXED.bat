@echo off
cd /d "%~dp0"
if not exist "run.py" goto missing
py -3 -c "import sys; sys.exit(sys.version_info < (3,10))" >nul 2>nul
if not errorlevel 1 goto launcher
python -c "import sys; sys.exit(sys.version_info < (3,10))" >nul 2>nul
if not errorlevel 1 goto standard
set "STOCKGUARD_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%STOCKGUARD_PY%" goto unavailable
"%STOCKGUARD_PY%" run.py
goto done
:launcher
py -3 run.py
goto done
:standard
python run.py
goto done
:missing
echo Put this BAT file in the same extracted folder as run.py.
goto done
:unavailable
echo Python 3.10 or newer was not found. Install Python and try again.
:done
pause
