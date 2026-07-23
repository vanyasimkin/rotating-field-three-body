param(
    [Parameter(Mandatory = $true)]
    [string]$SourceRoot,

    [string]$DestinationRoot = (Resolve-Path "$PSScriptRoot\..").Path,

    [switch]$Overwrite
)

$ErrorActionPreference = "Stop"

$source = (Resolve-Path $SourceRoot).Path
$destination = (Resolve-Path $DestinationRoot).Path
$backupStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = Join-Path $destination "source_backup\import_$backupStamp"
$scriptRoot = Join-Path $destination "scripts\research"

New-Item -ItemType Directory -Force $backupRoot | Out-Null
New-Item -ItemType Directory -Force $scriptRoot | Out-Null

$files = @(
    "run_delta3_offgrid_scm.py",
    "evaluate_delta3_offgrid.py",
    "step01_archive_baseline.py",
    "step02_analyze_offgrid_errors.py",
    "step03_retrain_surrogate_augmented.py",
    "step04_run_independent_test2.py",
    "step05_benchmark_end_to_end.py",
    "step06b_validate_random_clusters_n4_n6.py",
    "step07_build_refined_pair_map.py",
    "step08_validate_refined_pair_map.py",
    "step09_recompute_delta3_targets.py",
    "step10_apply_physical_interpolator.py",
    "step11_refresh_cluster_predictions.py",
    "step12_validate_cluster_interpolation.py",
    "check_stage1_dipole_mechanism.py",
    "run_stage1_followup_tests.py",
    "make_prl_figures_main.py",
    "make_prl_figures_supplementary.py"
)

$missing = @()
foreach ($name in $files) {
    $input = Join-Path $source $name
    if (-not (Test-Path $input)) {
        $missing += $name
        continue
    }

    Copy-Item $input (Join-Path $backupRoot $name) -Force
    $output = Join-Path $scriptRoot $name
    if ((Test-Path $output) -and -not $Overwrite) {
        throw "Destination exists: $output. Re-run with -Overwrite after reviewing the backup."
    }
    Copy-Item $input $output -Force
}

if ($missing.Count -gt 0) {
    Write-Warning ("Missing source files: " + ($missing -join ", "))
}

Write-Host "Imported research scripts to: $scriptRoot"
Write-Host "Backup saved to: $backupRoot"
Write-Host "Next checks:"
Write-Host "  python -m compileall -q src examples tests scripts/research"
Write-Host "  python -m pytest -q"
