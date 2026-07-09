@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-hardware-system.ps1"

if errorlevel 1 (
  echo.
  echo Failed to start the hardware system.
  pause
)
