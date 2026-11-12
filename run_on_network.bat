@echo off
REM Starts Record Keeper on this laptop (no Render needed) and lets other computers
REM and phones on the SAME Wi-Fi open it too. Keep the server window open while using it.
cd /d "%~dp0"
if not exist logs mkdir logs
set PGDIR=%USERPROFILE%\pgsql

echo Starting the database...
"%PGDIR%\bin\pg_ctl.exe" status -D "%PGDIR%\data" >nul 2>&1
if errorlevel 1 (
    powershell -NoProfile -Command "Start-Process -WindowStyle Hidden -FilePath \"$env:USERPROFILE\pgsql\bin\pg_ctl.exe\" -ArgumentList 'start','-D',\"$env:USERPROFILE\pgsql\data\",'-l',\"$env:USERPROFILE\pgsql\data\pg_server.log\",'-w','-t','180'" >nul 2>&1
)
:waitpg
"%PGDIR%\bin\pg_isready.exe" -h localhost -p 5432 >nul 2>&1
if errorlevel 1 ( timeout /t 3 /nobreak >nul & goto :waitpg )

echo Stopping any old server...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*manage.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1

echo Updating the database...
".venv\Scripts\python.exe" manage.py migrate --noinput > logs\run_on_network_log.txt 2>&1

REM Accept this laptop's Wi-Fi address as well as 127.0.0.1 (local network only).
set DJANGO_ALLOWED_HOSTS=*

for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and $_.PrefixOrigin -ne 'WellKnown' } | Sort-Object InterfaceMetric | Select-Object -First 1).IPAddress"`) do set LANIP=%%i

start "Record Keeper server (network)" cmd /k ".venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000"

echo Waiting for the server to start...
:waitweb
powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 http://127.0.0.1:8000/).StatusCode } catch { exit 1 }" >nul 2>&1
if errorlevel 1 ( timeout /t 2 /nobreak >nul & goto :waitweb )

if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" http://127.0.0.1:8000/
) else (
    start "" http://127.0.0.1:8000/
)

echo.
echo ============================================================
echo   Record Keeper is running.
echo.
echo   On this laptop:      http://127.0.0.1:8000
echo   On other devices:    http://%LANIP%:8000
echo   (phones and computers must be on the same Wi-Fi)
echo.
echo   If Windows asks about Python and the firewall, click
echo   "Allow access" so other devices can connect.
echo ============================================================
echo Address for other devices: http://%LANIP%:8000 >> logs\run_on_network_log.txt
pause
