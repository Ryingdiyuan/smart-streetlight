@echo off
chcp 65001 >nul
title Smart Streetlight System

setlocal enabledelayedexpansion

rem ========================================
rem Smart Streetlight System - one-click start
rem ========================================

set "BACKEND_DIR=%~dp0backend"
set "FRONTEND_DIR=%~dp0frontend"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=5173"
set "BACKEND_PYTHON=python"

if exist "%BACKEND_DIR%\.conda\python.exe" (
    set "BACKEND_PYTHON=%BACKEND_DIR%\.conda\python.exe"
) else if exist "%BACKEND_DIR%\.venv\Scripts\python.exe" (
    set "BACKEND_PYTHON=%BACKEND_DIR%\.venv\Scripts\python.exe"
)

echo ============================================
echo    Smart Streetlight System - Start
echo ============================================
echo.

rem ---- 1. Check backend dependencies ----
echo [1/4] Checking backend Python dependencies...
cd /d "%BACKEND_DIR%"
"%BACKEND_PYTHON%" -c "import fastapi, uvicorn" 2>nul
if !errorlevel! neq 0 (
    echo   [!] Missing dependencies, installing...
    "%BACKEND_PYTHON%" -m pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo   [ERROR] Failed to install backend dependencies.
        echo           Please run: cd backend ^&^& python -m pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo   [OK] Backend dependencies installed
) else (
    echo   [OK] Backend dependencies are ready
)

rem ---- 2. Check / create database ----
echo [2/4] Checking database...
set "MYSQL_HOST=127.0.0.1"
set "MYSQL_PORT=3306"
set "MYSQL_USER=root"
set "MYSQL_PASSWORD="
set "MYSQL_DATABASE=smart_streetlight"

if exist "%BACKEND_DIR%\.env" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%BACKEND_DIR%\.env") do (
        if /i "%%A"=="MYSQL_HOST" set "MYSQL_HOST=%%B"
        if /i "%%A"=="MYSQL_PORT" set "MYSQL_PORT=%%B"
        if /i "%%A"=="MYSQL_USER" set "MYSQL_USER=%%B"
        if /i "%%A"=="MYSQL_PASSWORD" set "MYSQL_PASSWORD=%%B"
        if /i "%%A"=="MYSQL_DATABASE" set "MYSQL_DATABASE=%%B"
    )
)

echo   Host: !MYSQL_HOST!:!MYSQL_PORT!
echo   Database: !MYSQL_DATABASE!

where mysql >nul 2>nul
if !errorlevel! neq 0 (
    echo   [!] mysql command was not found. Skipping database auto-check.
    echo       The backend will still try to connect using backend\.env settings.
) else (
    if "!MYSQL_PASSWORD!"=="" (
        mysql -h "!MYSQL_HOST!" -P "!MYSQL_PORT!" -u "!MYSQL_USER!" -e "CREATE DATABASE IF NOT EXISTS !MYSQL_DATABASE! DEFAULT CHARSET utf8mb4;" 2>nul
    ) else (
        mysql -h "!MYSQL_HOST!" -P "!MYSQL_PORT!" -u "!MYSQL_USER!" -p"!MYSQL_PASSWORD!" -e "CREATE DATABASE IF NOT EXISTS !MYSQL_DATABASE! DEFAULT CHARSET utf8mb4;" 2>nul
    )

    if !errorlevel! equ 0 (
        echo   [OK] Database is ready
    ) else (
        echo   [!] Cannot connect to MySQL with backend\.env settings.
        echo       Please confirm MySQL is running and !MYSQL_HOST!:!MYSQL_PORT! allows this computer to connect.
        echo       The backend may fail to start if the database connection is unavailable.
    )
)

rem ---- 3. Check frontend dependencies ----
echo [3/4] Checking frontend dependencies...
cd /d "%FRONTEND_DIR%"
if exist node_modules (
    echo   [OK] Frontend dependencies are ready
) else (
    echo   [!] Missing dependencies, installing...
    call npm install
    if !errorlevel! neq 0 (
        echo   [ERROR] Failed to install frontend dependencies.
        pause
        exit /b 1
    )
    echo   [OK] Frontend dependencies installed
)

rem ---- 4. Start services ----
echo [4/4] Starting services...
echo.

echo   ^> Starting backend http://localhost:%BACKEND_PORT% ...
cd /d "%BACKEND_DIR%"
start "smart-streetlight-backend" cmd /c ""%BACKEND_PYTHON%" -m uvicorn app.main:app --reload --host 0.0.0.0 --port %BACKEND_PORT% & pause"

timeout /t 3 /nobreak >nul

echo   ^> Starting frontend http://localhost:%FRONTEND_PORT% ...
cd /d "%FRONTEND_DIR%"
start "smart-streetlight-frontend" cmd /c "npm run dev -- --host 127.0.0.1 --port %FRONTEND_PORT% & pause"

echo.
echo ============================================
echo    Started
echo ============================================
echo.
echo   Frontend : http://localhost:%FRONTEND_PORT%
echo   Backend  : http://localhost:%BACKEND_PORT%
echo   API Docs : http://localhost:%BACKEND_PORT%/docs
echo.
echo   Close the backend/frontend windows to stop services.
echo.
echo ============================================
echo.
pause
