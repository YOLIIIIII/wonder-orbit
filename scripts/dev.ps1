param([switch]$Sqlite)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$uvPath = Join-Path $projectRoot '.tools/bootstrap/bin/uv.exe'
$nodeDir = Join-Path $projectRoot '.tools/node/node_modules/node/bin'
if (Test-Path -LiteralPath $nodeDir) { $env:PATH = "$nodeDir;$env:PATH" }
if (Test-Path -LiteralPath $uvPath) { $uv = $uvPath } else { $uv = 'uv' }
$env:UV_CACHE_DIR = Join-Path $projectRoot '.cache/uv'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $projectRoot '.tools/python'
$env:PYTHONPATH = Join-Path $projectRoot 'backend'
if ($Sqlite) { $env:DATABASE_URL = 'sqlite:///./wonder.db' }
& $uv sync --frozen --python 3.12
if ($LASTEXITCODE -ne 0) { throw 'uv sync failed' }
& $uv run --no-sync alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'migration failed' }
Write-Host 'Backend: http://127.0.0.1:8000/docs'
Write-Host 'In another terminal: cd frontend; npm run dev (Node 22 required)'
& $uv run --no-sync uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
