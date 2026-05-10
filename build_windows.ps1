$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $RootDir "frontend"
$BackendRequirements = Join-Path $RootDir "backend\requirements.txt"
$BuildTempDir = Join-Path $RootDir "build\tmp"
$VenvDir = Join-Path $RootDir "build\python-venv-copies"
$Python = Join-Path $VenvDir "Scripts\python.exe"
$Npm = "npm"
$AppName = "AZViewer"
$DistRoot = Join-Path $RootDir "dist"
$AppDistDir = Join-Path $DistRoot $AppName
$PortableZip = Join-Path $DistRoot "$AppName-windows-portable.zip"

New-Item -ItemType Directory -Path $BuildTempDir -Force | Out-Null
$env:TEMP = $BuildTempDir
$env:TMP = $BuildTempDir

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

function Test-PythonExecutable {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return $false
    }

    & $Path --version *> $null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    & $Path -m pip --version *> $null
    return $LASTEXITCODE -eq 0
}

function Assert-PathExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    if (-not (Test-Path $Path)) {
        throw "$Description was not found: $Path"
    }
}

function Assert-PythonRuntimeBundled {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DistributionDir
    )

    $runtimeSearchDirs = @($DistributionDir, (Join-Path $DistributionDir "_internal")) |
        Where-Object { Test-Path $_ }

    $pythonDll = @(
        foreach ($dir in $runtimeSearchDirs) {
            Get-ChildItem -Path $dir -Filter "python*.dll" -File -ErrorAction SilentlyContinue
        }
    )
    $standardLibrary = @(
        foreach ($dir in $runtimeSearchDirs) {
            Get-ChildItem -Path $dir -Filter "base_library.zip" -File -ErrorAction SilentlyContinue
        }
    )

    if ($pythonDll.Count -eq 0) {
        throw "Python runtime DLL was not bundled in $DistributionDir."
    }

    if ($standardLibrary.Count -eq 0) {
        throw "Python standard library archive was not bundled in $DistributionDir."
    }
}

if (-not (Test-PythonExecutable -Path $Python)) {
    if (Test-Path $VenvDir) {
        Write-Host "Removing broken build Python virtual environment..."
        Remove-Item -LiteralPath $VenvDir -Recurse -Force
    }

    Write-Host "Creating build Python virtual environment..."
    Invoke-CheckedCommand python -m venv --copies $VenvDir
}

Write-Host "Installing Python dependencies..."
Invoke-CheckedCommand $Python -m pip install --upgrade pip
Invoke-CheckedCommand $Python -m pip install -r $BackendRequirements pyinstaller

Write-Host "Installing frontend dependencies..."
Push-Location $FrontendDir
try {
    if (Test-Path (Join-Path $FrontendDir "package-lock.json")) {
        Invoke-CheckedCommand $Npm ci
    }
    else {
        Invoke-CheckedCommand $Npm install
    }

    Write-Host "Building frontend..."
    Invoke-CheckedCommand $Npm run build
}
finally {
    Pop-Location
}

Write-Host "Building Windows executable..."
Push-Location $RootDir
try {
    Invoke-CheckedCommand $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --onedir `
        --name $AppName `
        --windowed `
        --paths "backend" `
        --collect-all "webview" `
        --collect-all "PIL" `
        --add-data "frontend\dist;frontend\dist" `
        "backend\main.py"
}
finally {
    Pop-Location
}

Write-Host "Validating bundled Python runtime..."
Assert-PathExists -Path (Join-Path $AppDistDir "$AppName.exe") -Description "Application executable"
Assert-PythonRuntimeBundled -DistributionDir $AppDistDir

Write-Host "Creating portable distribution archive..."
if (Test-Path $PortableZip) {
    Remove-Item -LiteralPath $PortableZip -Force
}
Compress-Archive -Path $AppDistDir -DestinationPath $PortableZip -Force

Write-Host ""
Write-Host "Build complete: dist\$AppName\$AppName.exe"
Write-Host "Portable package: dist\$AppName-windows-portable.zip"
Write-Host "This package includes the PyInstaller-bundled Python runtime for PCs without Python installed."
