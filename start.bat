@echo off
chcp 65001 >nul
title 智慧路灯节能系统

setlocal enabledelayedexpansion

:: ========================================
:: 智慧路灯节能系统 - 一键启动脚本
:: ========================================

:: ---- 配置（可根据需要修改） ----
set BACKEND_DIR=%~dp0backend
set FRONTEND_DIR=%~dp0frontend
set BACKEND_PORT=8000
set FRONTEND_PORT=5173

echo ============================================
echo    智慧路灯节能系统 - 一键启动
echo ============================================
echo.

:: ---- 1. 检查后端依赖 ----
echo [1/4] 检查后端 Python 依赖...
cd /d "%BACKEND_DIR%"
python -c "import fastapi, uvicorn" 2>nul
if %errorlevel% neq 0 (
    echo   ! 缺少依赖，正在安装...
    python -m pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo   [错误] 依赖安装失败，请手动执行:
        echo     cd backend ^&^& pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo   [OK] 依赖安装完成
) else (
    echo   [OK] 依赖已就绪
)

:: ---- 2. 检查/创建数据库 ----
echo [2/4] 检查数据库...
mysql -u root -p123456 -e "CREATE DATABASE IF NOT EXISTS smart_streetlight DEFAULT CHARSET utf8mb4;" 2>nul
if %errorlevel% equ 0 (
    echo   [OK] 数据库已就绪
) else (
    echo   [!] 无法连接 MySQL，请确认 MySQL 已启动
    echo       启动后端后可能因数据库连接失败而报错
)

:: ---- 3. 检查前端依赖 ----
echo [3/4] 检查前端依赖...
cd /d "%FRONTEND_DIR%"
if exist node_modules (
    echo   [OK] 依赖已就绪
) else (
    echo   ! 缺少依赖，正在安装...
    call npm install
    if !errorlevel! neq 0 (
        echo   [错误] 前端依赖安装失败
        pause
        exit /b 1
    )
    echo   [OK] 前端依赖安装完成
)

:: ---- 4. 启动服务 ----
echo [4/4] 启动服务...
echo.

:: 启动后端
echo   ^> 启动后端 (http://localhost:%BACKEND_PORT%) ...
cd /d "%BACKEND_DIR%"
start "智慧路灯-后端" cmd /c "uvicorn app.main:app --reload --host 0.0.0.0 --port %BACKEND_PORT% & pause"

:: 等待 3 秒让后端先启动
timeout /t 3 /nobreak >nul

:: 启动前端
echo   ^> 启动前端 (http://localhost:%FRONTEND_PORT%) ...
cd /d "%FRONTEND_DIR%"
start "智慧路灯-前端" cmd /c "npm run dev & pause"

echo.
echo ============================================
echo    启动完成！
echo ============================================
echo.
echo   Frontend : http://localhost:%FRONTEND_PORT%
echo   Backend  : http://localhost:%BACKEND_PORT%
echo   API Docs : http://localhost:%BACKEND_PORT%/docs
echo.
echo   ^> 前端默认使用 Mock 模式，无需后端也可运行
echo   ^> 如需连接后端，修改 frontend/.env 中的
echo     VITE_SERVICE_MODE=api
echo.
echo   ^> 关闭窗口即可停止服务
echo.
echo ============================================
echo.
pause
\r