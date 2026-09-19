@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run START_WINDOWS.bat once first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" train.py
pause
