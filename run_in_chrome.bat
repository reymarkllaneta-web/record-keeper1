@echo off
REM Starts the system (PostgreSQL + Django server) and opens it in Google Chrome.
cd /d "%~dp0"
call start_all.bat
echo Waiting for the server to start...
:waitweb
powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 http://127.0.0.1:8000/).StatusCode } catch { exit 1 }" >nul 2>&1
if errorlevel 1 ( timeout /t 2 /nobreak >nul & goto :waitweb )
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" http://127.0.0.1:8000/
) else if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" http://127.0.0.1:8000/
) else (
    start "" http://127.0.0.1:8000/
)
