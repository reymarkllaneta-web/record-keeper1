@echo off
REM Runs every automated test on a throwaway database in XAMPP (MariaDB). XAMPP MySQL must be started.
REM Results: logs\test_results_mariadb.txt
cd /d "%~dp0..\.."
if not exist logs mkdir logs
set PYTHONPATH=%CD%;%CD%\scripts\testing
echo Running tests on XAMPP, please wait...
".venv\Scripts\python.exe" -u manage.py test accounts documents test_functions --settings=test_settings_mariadb -v 2 --noinput > logs\test_results_mariadb.txt 2>&1
echo EXIT CODE %ERRORLEVEL% >> logs\test_results_mariadb.txt
