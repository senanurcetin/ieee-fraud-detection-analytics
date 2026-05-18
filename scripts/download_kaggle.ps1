$ErrorActionPreference = "Stop"

$RawDir = Join-Path $PSScriptRoot "..\data\raw\kaggle_ieee_fraud"
New-Item -ItemType Directory -Force -Path $RawDir | Out-Null

kaggle competitions download -c ieee-fraud-detection -p $RawDir

$ZipPath = Join-Path $RawDir "ieee-fraud-detection.zip"
if (Test-Path $ZipPath) {
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $RawDir -Force
}

Get-ChildItem -Path $RawDir | Select-Object Name,Length,LastWriteTime
