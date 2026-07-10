param(
  [switch]$NoBrowser,
  [switch]$Preview
)

$ErrorActionPreference = "Stop"

function Test-PortListening {
  param(
    [Parameter(Mandatory = $true)]
    [int]$Port
  )

  return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Escape-SingleQuotes {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Value
  )

  return $Value.Replace("'", "''")
}

function Start-InNewWindow {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Title,
    [Parameter(Mandatory = $true)]
    [string]$WorkingDirectory,
    [Parameter(Mandatory = $true)]
    [string]$Command
  )

  if ($Preview) {
    Write-Host "[Preview] $Title"
    Write-Host "  cwd: $WorkingDirectory"
    Write-Host "  cmd: $Command"
    return
  }

  $safeWorkingDirectory = Escape-SingleQuotes $WorkingDirectory
  $safeTitle = Escape-SingleQuotes $Title
  $commandText = "Set-Location -LiteralPath '$safeWorkingDirectory'; try { `$Host.UI.RawUI.WindowTitle = '$safeTitle' } catch {}; $Command"

  Start-Process -FilePath "powershell.exe" `
    -WorkingDirectory $WorkingDirectory `
    -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $commandText) | Out-Null
}

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $rootDir "backend"
$hardwareDir = Join-Path $rootDir "hardware-frontend"
$condaPython = Join-Path $backendDir ".conda\python.exe"
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"
$backendPython = if (Test-Path -LiteralPath $condaPython) { $condaPython } else { $venvPython }

if (-not (Test-Path -LiteralPath $backendDir)) {
  throw "Missing backend directory: $backendDir"
}

if (-not (Test-Path -LiteralPath $hardwareDir)) {
  throw "Missing hardware-frontend directory: $hardwareDir"
}

if (-not (Test-Path -LiteralPath $backendPython)) {
  throw "Missing backend Python. Expected either $condaPython or $venvPython"
}

if (-not (Test-Path -LiteralPath (Join-Path $hardwareDir "package.json"))) {
  throw "Missing hardware-frontend package.json"
}

Write-Host ""
Write-Host "Starting smart streetlight hardware system..."
Write-Host "Root: $rootDir"
Write-Host ""

if (Test-PortListening -Port 8000) {
  Write-Host "[Skip] Backend already listening on http://localhost:8000/"
} else {
  Start-InNewWindow `
    -Title "smart-streetlight backend" `
    -WorkingDirectory $backendDir `
    -Command "& '$backendPython' -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
  Write-Host "[Start] Backend launching on http://localhost:8000/"
}

if (Test-PortListening -Port 5174) {
  Write-Host "[Skip] Hardware frontend already listening on http://localhost:5174/"
} else {
  Start-InNewWindow `
    -Title "smart-streetlight hardware-frontend" `
    -WorkingDirectory $hardwareDir `
    -Command "npm run dev -- --host 0.0.0.0 --port 5174"
  Write-Host "[Start] Hardware frontend launching on http://localhost:5174/"
}

if (-not $NoBrowser) {
  if ($Preview) {
    Write-Host "[Preview] Browser: http://localhost:5174/"
    Write-Host "[Preview] Browser: http://localhost:8000/docs"
  } else {
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:5174/" | Out-Null
    Start-Process "http://localhost:8000/docs" | Out-Null
  }
}

Write-Host ""
Write-Host "Done."
Write-Host "Hardware frontend: http://localhost:5174/"
Write-Host "Backend docs:       http://localhost:8000/docs"
Write-Host ""
