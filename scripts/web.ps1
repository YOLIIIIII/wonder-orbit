param([int]$Port = 5173)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$nodeDir = Join-Path $projectRoot '.tools/node/node_modules/node/bin'
if (Test-Path -LiteralPath $nodeDir) {
    $env:PATH = "$nodeDir;$env:PATH"
    $node = Join-Path $nodeDir 'node.exe'
} else { $node = 'node' }
$env:npm_config_cache = Join-Path $projectRoot '.cache/npm'
Set-Location -LiteralPath (Join-Path $projectRoot 'frontend')
if (-not (Test-Path -LiteralPath 'node_modules/vite/bin/vite.js')) {
    throw '请先在 frontend 运行 npm ci（Node 22）。'
}
& $node node_modules/vite/bin/vite.js --host 127.0.0.1 --port $Port
