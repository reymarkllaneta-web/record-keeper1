@echo off
cd /d "%~dp0..\.."
echo Saving the certified true copy PDF...
".venv\Scripts\python.exe" -u scripts\screenshots\download_ctc.py
echo Finished. You can close this window.
