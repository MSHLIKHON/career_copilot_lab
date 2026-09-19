@echo off
setlocal
cd /d "%~dp0"
title Career Copilot Lab - Team NO AI
if exist ".venv\Scripts\python.exe" goto ready
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 -m venv .venv
if errorlevel 1 goto failed
goto ready
:usepython
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
