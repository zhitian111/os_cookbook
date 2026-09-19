[CmdletBinding()]
param(
    [ValidateSet('all', 'combined', 'spec', 'lab-manual', 'clean')]
    [string]$Target = 'all'
)

$ErrorActionPreference = 'Stop'
$BuildDirectory = Join-Path $PSScriptRoot 'build'

if ($Target -eq 'clean') {
    if (Test-Path -LiteralPath $BuildDirectory) {
        Remove-Item -LiteralPath $BuildDirectory -Recurse -Force
    }
    exit 0
}

if (-not (Get-Command xelatex -ErrorAction SilentlyContinue)) {
    throw '找不到 xelatex。请安装 MiKTeX 或 TeX Live，或在 Overleaf 中选择 XeLaTeX。'
}

New-Item -ItemType Directory -Path $BuildDirectory -Force | Out-Null
$Documents = switch ($Target) {
    'all'        { @('main.tex', 'spec.tex', 'lab-manual.tex') }
    'combined'   { @('main.tex') }
    'spec'       { @('spec.tex') }
    'lab-manual' { @('lab-manual.tex') }
}

foreach ($Document in $Documents) {
    foreach ($Pass in 1..2) {
        & xelatex -interaction=nonstopmode -halt-on-error -file-line-error "-output-directory=$BuildDirectory" $Document
        if ($LASTEXITCODE -ne 0) {
            throw "$Document 编译失败（第 $Pass 次）。"
        }
    }
}
