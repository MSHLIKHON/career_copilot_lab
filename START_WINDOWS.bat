@echo off
setlocal
cd /d "%~dp0"
title Career Copilot Lab - Team NO AI
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info[:2] in ((3,11),(3,12),(3,13)) else 1)" >nul 2>nul
  if errorlevel 1 goto badvenv
  goto ready
)
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3.12 -m venv .venv >nul 2>nul
if not errorlevel 1 goto ready
py -3.13 -m venv .venv >nul 2>nul
if not errorlevel 1 goto ready
py -3.11 -m venv .venv >nul 2>nul
if not errorlevel 1 goto ready
:usepython
python -c "import sys; raise SystemExit(0 if sys.version_info[:2] in ((3,11),(3,12),(3,13)) else 1)" >nul 2>nul
if errorlevel 1 goto nopython
python -m venv .venv
if errorlevel 1 goto failed
:ready
".venv\Scripts\python.exe" bootstrap.py
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo Setup or launch failed. Read the error above.
echo Install Python 3.12 and tick "Add Python to PATH".
echo See START_HERE_BANGLA.md for help. Do not close this window before taking a screenshot.
pause
exit /b 1
:badvenv
echo.
echo The existing .venv uses an unsupported Python version.
echo Delete the .venv folder, install Python 3.12, and run this file again.
pause
exit /b 1
:nopython
echo.
echo Python 3.12 is recommended. Supported versions are 3.11 through 3.13.
echo Install Python 3.12 and tick "Add Python to PATH".
pause
exit /b 1
