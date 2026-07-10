@echo off
chcp 65001 >nul
cd /d "%~dp0"
start "smart-streetlight-backend" "%~dp0run-backend.bat"
timeout /t 5 /nobreak >nul
start "smart-streetlight-frontend" "%~dp0run-frontend.bat"
echo Backend:  http://127.0.0.1:8000
echo API Docs: http://127.0.0.1:8000/docs
echo Frontend: http://127.0.0.1:5173
pause
