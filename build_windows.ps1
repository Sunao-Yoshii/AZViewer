$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $RootDir "frontend"
$BackendRequirements = Join-Path $RootDir "backend\requirements.txt"
$LocalBuildRoot = Join-Path $env:LOCALAPPDATA "AZViewer\build"
$BuildTempDir = Join-Path $LocalBuildRoot "tmp"
$PyInstallerWorkDir = Join-Path $LocalBuildRoot "pyinstaller-work"
$VenvDir = Join-Path $RootDir "build\python-venv-copies"
$Python = Join-Path $VenvDir "Scripts\python.exe"
$BootstrapPython = "C:\Python312\python.exe"
$Npm = "npm"
$PyInstallerPackage = "pyinstaller==6.20.0"
$AppName = "AZViewer"
$DistRoot = Join-Path $RootDir "dist"
$AppDistDir = Join-Path $DistRoot $AppName
$PortableZip = Join-Path $DistRoot "$AppName-windows-portable.zip"

New-Item -ItemType Directory -Path $BuildTempDir -Force | Out-Null
New-Item -ItemType Directory -Path $PyInstallerWorkDir -Force | Out-Null
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

function Remove-DirectoryIfExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return
    }

    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
            return
        }
        catch {
            if ($attempt -eq 5) {
                throw
            }

            Start-Sleep -Milliseconds (300 * $attempt)
        }
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

function Test-VenvUsesBootstrapPython {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$ExpectedBaseDir
    )

    if (-not (Test-PythonExecutable -Path $Path)) {
        return $false
    }

    $actualBaseDir = & $Path -c "import os, sys; print(os.path.normcase(os.path.abspath(sys.base_prefix)))"
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    $expected = [System.IO.Path]::GetFullPath($ExpectedBaseDir).TrimEnd("\")
    $actual = [System.IO.Path]::GetFullPath($actualBaseDir.Trim()).TrimEnd("\")
    return $actual -ieq $expected
}

function Assert-BuildPythonRuntime {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $script = @"
import platform
import sys

if platform.architecture()[0] != "64bit":
    raise SystemExit("Build Python must be 64-bit.")

print(sys.version)
print(platform.architecture()[0])

import clr
print("pythonnet import ok")
"@

    $script | & $Path -
    if ($LASTEXITCODE -ne 0) {
        throw "Build Python cannot import pythonnet/clr. Recreate the build environment before packaging."
    }
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

function Assert-BundledFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        throw "Required bundled file was not found: $Path"
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

function Assert-PythonNetBundled {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DistributionDir
    )

    $internalDir = Join-Path $DistributionDir "_internal"

    Assert-BundledFile -Path (Join-Path $internalDir "pythonnet\runtime\Python.Runtime.dll")
    Assert-BundledFile -Path (Join-Path $internalDir "pythonnet\runtime\Python.Runtime.deps.json")
    Assert-BundledFile -Path (Join-Path $internalDir "clr_loader\ffi\dlls\amd64\ClrLoader.dll")
}

function Assert-WindowsGuiRuntimeBundled {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DistributionDir
    )

    $internalDir = Join-Path $DistributionDir "_internal"

    Assert-BundledFile -Path (Join-Path $internalDir "webview\lib\Microsoft.Web.WebView2.Core.dll")
    Assert-BundledFile -Path (Join-Path $internalDir "webview\lib\Microsoft.Web.WebView2.WinForms.dll")
    Assert-BundledFile -Path (Join-Path $internalDir "webview\lib\runtimes\win-x64\native\WebView2Loader.dll")
    Assert-BundledFile -Path (Join-Path $internalDir "VCRUNTIME140.dll")
    Assert-BundledFile -Path (Join-Path $internalDir "VCRUNTIME140_1.dll")
    Assert-BundledFile -Path (Join-Path $internalDir "ucrtbase.dll")
}

Assert-PathExists -Path $BootstrapPython -Description "Bootstrap Python executable"
$BootstrapPythonBaseDir = Split-Path -Parent $BootstrapPython
$shouldCreateVenv = -not (Test-VenvUsesBootstrapPython -Path $Python -ExpectedBaseDir $BootstrapPythonBaseDir)

if ($shouldCreateVenv) {
    if (Test-Path $VenvDir) {
        Write-Host "Removing stale build Python virtual environment..."
        Remove-DirectoryIfExists -Path $VenvDir
    }

    Write-Host "Creating build Python virtual environment..."
    Invoke-CheckedCommand $BootstrapPython -m venv --copies $VenvDir
}

Write-Host "Installing Python dependencies..."
Invoke-CheckedCommand $Python -m pip install --upgrade pip
Invoke-CheckedCommand $Python -m pip install -r $BackendRequirements $PyInstallerPackage
Assert-BuildPythonRuntime -Path $Python

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
if (Test-Path $AppDistDir) {
    Write-Host "Removing previous application distribution..."
    Remove-DirectoryIfExists -Path $AppDistDir
}
Write-Host "Preparing PyInstaller work directory..."
Remove-DirectoryIfExists -Path $PyInstallerWorkDir
New-Item -ItemType Directory -Path $PyInstallerWorkDir -Force | Out-Null

Push-Location $RootDir
try {
    Invoke-CheckedCommand $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --onedir `
        --noupx `
        --workpath $PyInstallerWorkDir `
        --name $AppName `
        --windowed `
        --paths "backend" `
        --collect-all "webview" `
        --collect-all "pythonnet" `
        --collect-all "clr_loader" `
        --collect-all "cffi" `
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
Assert-PythonNetBundled -DistributionDir $AppDistDir
Assert-WindowsGuiRuntimeBundled -DistributionDir $AppDistDir

Write-Host "Running packaged runtime smoke test..."
Invoke-CheckedCommand (Join-Path $AppDistDir "$AppName.exe") --smoke-test-runtime

Write-Host "Creating portable distribution archive..."
if (Test-Path $PortableZip) {
    Remove-Item -LiteralPath $PortableZip -Force
}
Compress-Archive -Path $AppDistDir -DestinationPath $PortableZip -Force

Write-Host ""
Write-Host "Build complete: dist\$AppName\$AppName.exe"
Write-Host "Portable package: dist\$AppName-windows-portable.zip"
Write-Host "This package includes the PyInstaller-bundled Python runtime for PCs without Python installed."
