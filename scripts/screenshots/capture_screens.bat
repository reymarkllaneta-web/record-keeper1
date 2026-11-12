@echo off
REM Takes screenshots of every page for each role (needs the server running: run_in_chrome.bat).
REM Pictures: scripts\screenshots\out
cd /d "%~dp0..\.."
echo Installing the screenshot tool (first time only)...
".venv\Scripts\python.exe" -m pip install -q playwright > scripts\screenshots\pip_log.txt 2>&1
echo Taking screenshots, please wait...
".venv\Scripts\python.exe" -u scripts\screenshots\capture.py
echo.
echo Finished. You can close this window.
