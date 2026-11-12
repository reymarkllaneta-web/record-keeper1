@echo off
REM Moves Record Keeper's data from PostgreSQL to XAMPP (MariaDB). Safe to run again.
REM Before running: open the XAMPP Control Panel and click Start beside MySQL.
REM Results: logs\xampp_move_log.txt
cd /d "%~dp0..\.."
if not exist logs mkdir logs
if not exist backups mkdir backups
set LOG=logs\xampp_move_log.txt
set PY=.venv\Scripts\python.exe
REM Save and read the backup as UTF-8 so dashes, the enye (n with tilde) and other symbols survive.
set PYTHONUTF8=1
echo Moving Record Keeper to XAMPP. Please wait, this takes a few minutes...
echo === Record Keeper: move to XAMPP (%date% %time%) === > %LOG%

echo [1/8] Installing the MariaDB driver (PyMySQL)...
echo --- [1/8] install PyMySQL --- >> %LOG%
%PY% -m pip install "PyMySQL>=1.1" >> %LOG% 2>&1
if errorlevel 1 goto :failed

echo [2/8] Starting PostgreSQL to read the current records...
echo --- [2/8] start PostgreSQL --- >> %LOG%
set PGDIR=%USERPROFILE%\pgsql
"%PGDIR%\bin\pg_ctl.exe" status -D "%PGDIR%\data" >nul 2>&1
if errorlevel 1 (
    powershell -NoProfile -Command "Start-Process -WindowStyle Hidden -FilePath \"$env:USERPROFILE\pgsql\bin\pg_ctl.exe\" -ArgumentList 'start','-D',\"$env:USERPROFILE\pgsql\data\",'-l',\"$env:USERPROFILE\pgsql\data\pg_server.log\",'-w','-t','180'" >> %LOG% 2>&1
)
:waitpg
"%PGDIR%\bin\pg_isready.exe" -h localhost -p 5432 >nul 2>&1
if errorlevel 1 ( timeout /t 3 /nobreak >nul & goto :waitpg )

echo [3/8] Backing up every record from PostgreSQL...
echo --- [3/8] backup from PostgreSQL --- >> %LOG%
set DB_ENGINE=postgresql
%PY% manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission -e sessions --indent 1 -o backups\postgres_backup.json >> %LOG% 2>&1
if errorlevel 1 goto :failed
%PY% scripts\database\xampp_tools.py count backups\count_postgres.json >> %LOG% 2>&1
if errorlevel 1 goto :failed

echo [4/8] Creating the database in XAMPP...
echo --- [4/8] create database in XAMPP --- >> %LOG%
set DB_ENGINE=mysql
%PY% scripts\database\xampp_tools.py createdb >> %LOG% 2>&1
if errorlevel 1 goto :failed

echo [5/8] Creating the tables in XAMPP...
echo --- [5/8] migrate --- >> %LOG%
%PY% manage.py migrate --noinput >> %LOG% 2>&1
if errorlevel 1 goto :failed
%PY% manage.py flush --no-input >> %LOG% 2>&1
if errorlevel 1 goto :failed

echo [6/8] Copying the records into XAMPP...
echo --- [6/8] load records --- >> %LOG%
%PY% manage.py loaddata backups\postgres_backup.json >> %LOG% 2>&1
if errorlevel 1 goto :failed

echo [7/8] Checking that every table matches...
echo --- [7/8] compare --- >> %LOG%
%PY% scripts\database\xampp_tools.py count backups\count_xampp.json >> %LOG% 2>&1
%PY% scripts\database\xampp_tools.py compare backups\count_postgres.json backups\count_xampp.json >> %LOG% 2>&1
if errorlevel 1 goto :failed

echo [8/8] Switching Record Keeper to XAMPP...
echo --- [8/8] switch .env --- >> %LOG%
%PY% scripts\database\xampp_tools.py use-mysql >> %LOG% 2>&1
echo DONE >> %LOG%
echo.
echo Finished. Record Keeper now uses XAMPP. Details: %LOG%
pause
goto :eof

:failed
echo FAILED >> %LOG%
echo.
echo Something went wrong. Nothing was switched; the system still uses PostgreSQL.
echo Open %LOG% to see why, or tell Claude.
pause
