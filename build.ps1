# Build YouTubeNotifier.exe
# Usage:  .\build.ps1
# Output: dist\YouTubeNotifier.exe

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step($n, $msg) {
    Write-Host ""
    Write-Host "[$n] $msg" -ForegroundColor Cyan
}

Write-Host "============================================" -ForegroundColor Yellow
Write-Host "  YouTube Notifier – PyInstaller Build"     -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Yellow

# ── 0. Sanity checks ────────────────────────────────────────────────────────
Write-Step 0 "Checking prerequisites"

$python = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $python) { throw "python not found in PATH" }
Write-Host "  Python: $($python.Source)"

$pyinstaller = python -c "import PyInstaller; print(PyInstaller.__version__)" 2>$null
if (-not $pyinstaller) {
    Write-Host "  PyInstaller not found – installing..." -ForegroundColor Yellow
    python -m pip install pyinstaller --quiet
}
Write-Host "  PyInstaller: $pyinstaller"

# ── 1. Generate icon ─────────────────────────────────────────────────────────
Write-Step 1 "Generating icon (resources\icon.ico)"
python create_icon.py
if ($LASTEXITCODE -ne 0) { throw "Icon generation failed" }

# ── 2. client_secrets.json warning ───────────────────────────────────────────
Write-Step 2 "Checking client_secrets.json"
$secretsPath = "$env:APPDATA\YouTubeNotifier\client_secrets.json"
if (Test-Path $secretsPath) {
    Write-Host "  Found: $secretsPath  (will be bundled)" -ForegroundColor Green
} else {
    Write-Host "  WARNING: $secretsPath not found." -ForegroundColor Yellow
    Write-Host "  The .exe will work but users must place client_secrets.json" -ForegroundColor Yellow
    Write-Host "  in %APPDATA%\YouTubeNotifier\ before first launch." -ForegroundColor Yellow
}

# ── 3. Clean previous build ───────────────────────────────────────────────────
Write-Step 3 "Cleaning previous build artefacts"
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "dist\YouTubeNotifier.exe") { Remove-Item "dist\YouTubeNotifier.exe" -Force }

# ── 4. PyInstaller ────────────────────────────────────────────────────────────
Write-Step 4 "Running PyInstaller"
python -m PyInstaller build.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit code $LASTEXITCODE)" }

# ── 5. Report ─────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Build complete!" -ForegroundColor Green
$exe = Get-Item "dist\YouTubeNotifier.exe" -ErrorAction SilentlyContinue
if ($exe) {
    $mb = [math]::Round($exe.Length / 1MB, 1)
    Write-Host "  Output : $($exe.FullName)" -ForegroundColor Green
    Write-Host "  Size   : $mb MB" -ForegroundColor Green
} else {
    Write-Host "  WARNING: dist\YouTubeNotifier.exe not found after build!" -ForegroundColor Red
}
Write-Host "============================================" -ForegroundColor Green
