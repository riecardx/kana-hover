$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$target = Join-Path $root 'vendor\python'
New-Item -Path $target -ItemType Directory -Force | Out-Null
python -m pip install --target $target -r (Join-Path $root 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw "Python dependency installation failed" }

$from = 'C:\Program Files\Tesseract-OCR'
$to = Join-Path $root 'vendor\tesseract'
if (!(Test-Path (Join-Path $to 'tesseract.exe'))) {
    if (!(Test-Path (Join-Path $from 'tesseract.exe'))) {
        throw "Install Tesseract locally before preparing vendor\tesseract"
    }
    New-Item -Path $to -ItemType Directory -Force | Out-Null
    Copy-Item (Join-Path $from 'tesseract.exe') $to
    Get-ChildItem $from -Filter '*.dll' -File | Copy-Item -Destination $to
}
if (!(Test-Path (Join-Path $root 'tessdata\jpn.traineddata'))) {
    throw "Missing project OCR model tessdata\jpn.traineddata"
}
Write-Host 'Project-local Python, dictionary, OCR, and OpenJTalk dependencies prepared.'
