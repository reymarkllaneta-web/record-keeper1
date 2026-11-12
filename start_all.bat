@echo off
REM Starts the database in the background (safe to close windows afterwards), then starts the Django server.
REM Uses XAMPP's MySQL (MariaDB) when .env says DB_ENGINE=mysql, otherwise PostgreSQL.
cd /d "%~dp0"
if not exist logs mkdir logs
findstr /b /i /c:"DB_ENGINE=mysql" .env >nul 2>&1
if not errorlevel 1 goto :xampp
set PGDIR=%USERPROFILE%\pgsql
echo === PostgreSQL === > logs\start_all_log.txt
"%PGDIR%\bin\pg_ctl.exe" status -D "%PGDIR%\data" >nul 2>&1
if errorlevel 1 (
    echo starting in background... >> logs\start_all_log.txt
    powershell -NoProfile -Command "Start-Process -WindowStyle Hidden -FilePath \"$env:USERPROFILE\pgsql\bin\pg_ctl.exe\" -ArgumentList 'start','-D',\"$env:USERPROFILE\pgsql\data\",'-l',\"$env:USERPROFILE\pgsql\data\pg_server.log\",'-w','-t','180'" >> logs\start_all_log.txt 2>&1
)
:waitpg
"%PGDIR%\bin\pg_isready.exe" -h localhost -p 5432 >nul 2>&1
if errorlevel 1 ( timeout /t 3 /nobreak >nul & goto :waitpg )
"%PGDIR%\bin\pg_ctl.exe" status -D "%PGDIR%\data" >> logs\start_all_log.txt 2>&1
goto :django

:xampp
echo === XAMPP MySQL (MariaDB) === > logs\start_all_log.txt
"C:\xampp\mysql\bin\mysqladmin.exe" -u root -h 127.0.0.1 ping >nul 2>&1
if errorlevel 1 (
    echo starting XAMPP MySQL in background... >> logs\start_all_log.txt
    powershell -NoProfile -Command "Start-Process -WindowStyle Hidden -WorkingDirectory 'C:\xampp' -FilePath 'C:\xampp\mysql\bin\mysqld.exe' -ArgumentList '--defaults-file=C:\xampp\mysql\bin\my.ini','--standalone'" >> logs\start_all_log.txt 2>&1
)
:waitmy
"C:\xampp\mysql\bin\mysqladmin.exe" -u root -h 127.0.0.1 ping >nul 2>&1
if errorlevel 1 ( timeout /t 2 /nobreak >nul & goto :waitmy )
echo XAMPP MySQL is running >> logs\start_all_log.txt

:django
echo === stopping old Django processes === >> logs\start_all_log.txt
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*manage.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; 'stopped ' + $_.ProcessId }" >> logs\start_all_log.txt 2>&1
call ".venv\Scripts\activate.bat"
echo === database check === >> logs\start_all_log.txt
python -u -c "import os,django;os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings');django.setup();from django.db import connection as c;c.ensure_connection();print('engine:',c.vendor,'database:',c.settings_dict['NAME']);from accounts.models import User;print('accounts:',User.objects.count());print('active+approved:',User.objects.filter(is_active=True,approval_status='APPROVED').count())" >> logs\start_all_log.txt 2>&1
echo === migrate === >> logs\start_all_log.txt
python manage.py migrate --noinput >> logs\start_all_log.txt 2>&1
echo === Recycle Bin clean-up (records older than 30 days) === >> logs\start_all_log.txt
python manage.py purge_recycle_bin >> logs\start_all_log.txt 2>&1
echo === starting server === >> logs\start_all_log.txt
start "Records Archive server" cmd /k ".venv\Scripts\python.exe manage.py runserver"
echo === done === >> logs\start_all_log.txt
