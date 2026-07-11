@echo off
chcp 65001 >nul
cd /d "%~dp0backend"
set "PATH=%CD%\.conda;%CD%\.conda\Scripts;%CD%\.conda\Library\bin;%PATH%"
".conda\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
