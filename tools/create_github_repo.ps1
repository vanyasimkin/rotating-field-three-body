param(
    [string]$Repository = "vanyasimkin/rotating-field-three-body",
    [switch]$Private
)

$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path "$PSScriptRoot\..").Path

if (-not (Test-Path ".git")) {
    git init
    git branch -M main
}

python -m compileall -q src examples tests
python -m pytest -q

git add .
if ((git status --porcelain).Length -gt 0) {
    git commit -m "Initial public reproducibility release"
}

$visibility = if ($Private) { "--private" } else { "--public" }
$existingRemote = git remote 2>$null
if ($existingRemote -contains "origin") {
    Write-Host "Remote origin already exists. Pushing current main branch."
    git push -u origin main
} else {
    gh auth status
    gh repo create $Repository $visibility --source . --remote origin --push
}
