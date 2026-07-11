@echo off
chcp 65001 >nul
title Smart Streetlight System

setlocal enabledelayedexpansion

set "BACKEND_DIR=%~dp0backend"
set "FRONTEND_DIR=%~dp0frontend"
set "HARDWARE_FRONTEND_DIR=%~dp0hardware-frontend"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=5173"
set "HARDWARE_FRONTEND_PORT=5174"
set "BACKEND_HOST=0.0.0.0"
set "FRONTEND_HOST=0.0.0.0"
set "HARDWARE_FRONTEND_HOST=0.0.0.0"
set "BACKEND_PYTHON=python"
set "CONDA_BACKEND_PYTHON=%BACKEND_DIR%\.conda\python.exe"
set "VENV_BACKEND_PYTHON=%BACKEND_DIR%\.venv\Scripts\python.exe"

if exist "%CONDA_BACKEND_PYTHON%" (
    "%CONDA_BACKEND_PYTHON%" -c "import sys" >nul 2>nul
    if !errorlevel! equ 0 (
        set "BACKEND_PYTHON=%CONDA_BACKEND_PYTHON%"
    )
)
if "%BACKEND_PYTHON%"=="python" if exist "%VENV_BACKEND_PYTHON%" (
    "%VENV_BACKEND_PYTHON%" -c "import sys" >nul 2>nul
    if !errorlevel! equ 0 (
        set "BACKEND_PYTHON=%VENV_BACKEND_PYTHON%"
    )
)

echo ============================================
echo    Smart Streetlight System - Start
echo ============================================
echo.

if not exist "%BACKEND_DIR%" (
    echo [ERROR] Missing backend directory: %BACKEND_DIR%
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%" (
    echo [ERROR] Missing frontend directory: %FRONTEND_DIR%
    pause
    exit /b 1
)

if not exist "%HARDWARE_FRONTEND_DIR%" (
    echo [ERROR] Missing hardware-frontend directory: %HARDWARE_FRONTEND_DIR%
    pause
    exit /b 1
)

rem ---- 1. Check backend dependencies ----
echo [1/5] Checking backend Python dependencies...
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
echo [2/5] Checking database...
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
echo [3/5] Checking frontend dependencies...
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

rem ---- 4. Check hardware frontend dependencies ----
echo [4/5] Checking hardware frontend dependencies...
cd /d "%HARDWARE_FRONTEND_DIR%"
if exist node_modules (
    echo   [OK] Hardware frontend dependencies are ready
) else (
    echo   [!] Missing dependencies, installing...
    call npm install
    if !errorlevel! neq 0 (
        echo   [ERROR] Failed to install hardware frontend dependencies.
        pause
        exit /b 1
    )
    echo   [OK] Hardware frontend dependencies installed
)

rem ---- 5. Start services ----
echo [5/5] Starting services...
echo.

call :check_port %BACKEND_PORT%
if !errorlevel! equ 0 (
    echo   [SKIP] Backend is already listening on http://localhost:%BACKEND_PORT%
) else (
    echo   ^> Starting backend http://localhost:%BACKEND_PORT% ...
    cd /d "%BACKEND_DIR%"
    set "WINDOW_DIR=%BACKEND_DIR%"
    set "WINDOW_COMMAND=""%BACKEND_PYTHON%"" -m uvicorn app.main:app --reload --host %BACKEND_HOST% --port %BACKEND_PORT%"
    call :start_window
    timeout /t 2 /nobreak >nul
)

call :check_port %FRONTEND_PORT%
if !errorlevel! equ 0 (
    echo   [SKIP] Frontend is already listening on http://localhost:%FRONTEND_PORT%
) else (
    echo   ^> Starting frontend http://localhost:%FRONTEND_PORT% ...
    cd /d "%FRONTEND_DIR%"
    set "WINDOW_DIR=%FRONTEND_DIR%"
    set "WINDOW_COMMAND=npm run dev -- --host %FRONTEND_HOST% --port %FRONTEND_PORT%"
    call :start_window
    timeout /t 2 /nobreak >nul
)

call :check_port %HARDWARE_FRONTEND_PORT%
if !errorlevel! equ 0 (
    echo   [SKIP] Hardware frontend is already listening on http://localhost:%HARDWARE_FRONTEND_PORT%
) else (
    echo   ^> Starting hardware frontend http://localhost:%HARDWARE_FRONTEND_PORT% ...
    cd /d "%HARDWARE_FRONTEND_DIR%"
    set "WINDOW_DIR=%HARDWARE_FRONTEND_DIR%"
    set "WINDOW_COMMAND=npm run dev -- --host %HARDWARE_FRONTEND_HOST% --port %HARDWARE_FRONTEND_PORT%"
    call :start_window
    timeout /t 2 /nobreak >nul
)

echo.
echo   ^> Opening browser pages...
set "OPEN_URL=http://localhost:%FRONTEND_PORT%"
call :open_url
set "OPEN_URL=http://localhost:%HARDWARE_FRONTEND_PORT%"
call :open_url
set "OPEN_URL=http://localhost:%BACKEND_PORT%/docs"
call :open_url

echo.
echo ============================================
echo    Started
echo ============================================
echo.
echo   Frontend : http://localhost:%FRONTEND_PORT%
echo   Hardware : http://localhost:%HARDWARE_FRONTEND_PORT%
echo   Backend  : http://localhost:%BACKEND_PORT%
echo   API Docs : http://localhost:%BACKEND_PORT%/docs
echo.
echo   Close the backend/frontend windows to stop services.
echo.
echo ============================================
echo.
pause
exit /b 0

:check_port
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort %1 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" >nul 2>nul
exit /b %errorlevel%

:start_window
powershell -NoProfile -ExecutionPolicy Bypass -Command "$wd = $env:WINDOW_DIR; $cmd = $env:WINDOW_COMMAND; Start-Process -FilePath 'cmd.exe' -WorkingDirectory $wd -ArgumentList '/k', $cmd | Out-Null" >nul 2>nul
exit /b %errorlevel%

:open_url
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process $env:OPEN_URL | Out-Null" >nul 2>nul
exit /b %errorlevel%
