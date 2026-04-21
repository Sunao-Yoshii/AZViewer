$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $RootDir "frontend"
$BackendRequirements = Join-Path $RootDir "backend\requirements.txt"
$Python = Join-Path $RootDir ".venv\Scripts\python.exe"
$Npm = "npm"

if (-not (Test-Path $Python)) {
    Write-Host "Creating Python virtual environment..."
    python -m venv (Join-Path $RootDir ".venv")
}

Write-Host "Installing Python dependencies..."
& $Python -m pip install --upgrade pip
& $Python -m pip install -r $BackendRequirements pyinstaller

Write-Host "Installing frontend dependencies..."
Push-Location $FrontendDir
try {
    if (Test-Path (Join-Path $FrontendDir "package-lock.json")) {
        & $Npm ci
    }
    else {
        & $Npm install
    }

    Write-Host "Building frontend..."
    & $Npm run build
}
finally {
    Pop-Location
}

Write-Host "Building Windows executable..."
Push-Location $RootDir
try {
    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --name "AZViewer" `
        --windowed `
        --paths "backend" `
        --collect-submodules "webview" `
        --add-data "frontend\dist;frontend\dist" `
        "backend\main.py"
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Build complete: dist\AZViewer\AZViewer.exe"
