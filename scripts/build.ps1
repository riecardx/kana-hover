$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $root
try {
    $env:PYTHONPATH = (Join-Path $root 'vendor\python') + ';' +
        (Join-Path $root 'vendor\python\win32') + ';' +
        (Join-Path $root 'vendor\python\win32\lib') + ';' +
        (Join-Path $root 'vendor\python\pywin32_system32')
    $spec = Join-Path $root 'KanaHover.spec'
    python -m PyInstaller --noconfirm --clean --workpath (Join-Path $root 'build') --distpath (Join-Path $root 'releases') $spec
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed' }
    $release = Join-Path $root 'releases\KanaHover-0.7.1-20261104'
    Copy-Item -LiteralPath (Join-Path $root 'README.md') -Destination (Join-Path $release 'README.md') -Force
    $instructions = Get-ChildItem -LiteralPath (Join-Path $root 'docs') -Filter '*.txt' -File | Select-Object -First 1
    if ($instructions) { Copy-Item -LiteralPath $instructions.FullName -Destination (Join-Path $release 'QuickStart.txt') -Force }
    foreach ($name in @('ocr_settings.json','voice_settings.json')) {
        $source = Join-Path $root $name
        if (Test-Path -LiteralPath $source) {
            Copy-Item -LiteralPath $source -Destination (Join-Path $release $name) -Force
        }
    }
    Write-Host 'Build complete; packaged EXE has not been launched.'
} finally {
    Pop-Location
}
