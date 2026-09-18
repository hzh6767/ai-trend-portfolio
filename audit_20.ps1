param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$projects = @(Get-ChildItem $root -Directory | Where-Object { $_.Name -notin @(".git", ".github") })
if ($projects.Count -ne 10) { throw "Expected 10 projects, found $($projects.Count)" }

function Assert-StaticSafety {
    $codeRoots = $projects | ForEach-Object { Join-Path $_.FullName "src" }
    $forbidden = '(?i)(import\s+(requests|httpx|urllib3|boto3)|from\s+(requests|httpx|urllib3|boto3)|\b(socket|subprocess)\.|os\.system|eval\(|exec\(|pickle\.loads|yaml\.load\()'
    $hits = @(rg -n $forbidden $codeRoots -g '*.py' 2>$null)
    if ($hits.Count -gt 0) { throw "forbidden runtime call/import: $($hits -join '; ')" }
    $secretHits = @(rg -n '(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,})' $root -g '*.py' -g '*.json' -g '*.yml' -g '*.yaml' 2>$null)
    if ($secretHits.Count -gt 0) { throw "credential-shaped literal found" }
}

function Assert-Structure {
    foreach ($project in $projects) {
        foreach ($required in @("README.md", "pyproject.toml", "src", "tests")) {
            if (-not (Test-Path (Join-Path $project.FullName $required))) { throw "missing $required in $($project.Name)" }
        }
        $package = Get-ChildItem (Join-Path $project.FullName "src") -Directory | Select-Object -First 1
        if (-not $package) { throw "missing source package in $($project.Name)" }
        foreach ($entry in @("__init__.py", "__main__.py")) {
            if (-not (Test-Path (Join-Path $package.FullName $entry))) { throw "missing $entry in $($project.Name)" }
        }
        if (@(Get-ChildItem (Join-Path $project.FullName "tests") -Filter 'test_*.py').Count -eq 0) { throw "no tests in $($project.Name)" }
    }
}

function Assert-Behavior {
    & (Join-Path $root "run_all_checks.ps1") -Python $Python
    if ($LASTEXITCODE -ne 0) { throw "full test/demo run failed" }
}

function Assert-Hygiene {
    $conflicts = @(rg -n '^(<<<<<<<|=======|>>>>>>>)' $root -g '!*.pyc' 2>$null)
    if ($conflicts.Count -gt 0) { throw "merge conflict marker found" }
    $tmp = @(Get-ChildItem $root -Recurse -Force -File | Where-Object { $_.Name -match '\.(tmp|secret|key)$' })
    if ($tmp.Count -gt 0) { throw "temporary or secret-shaped file found: $($tmp.Name -join ', ')" }
    & git -C $root diff --check
    if ($LASTEXITCODE -ne 0) { throw "git diff --check failed" }
}

for ($round = 1; $round -le 5; $round++) {
    Assert-StaticSafety
    Write-Host "AUDIT $round/5 STATIC PASS"
    Assert-Structure
    Write-Host "AUDIT $round/5 STRUCTURE PASS"
    Assert-Behavior
    Write-Host "AUDIT $round/5 BEHAVIOR PASS"
    Assert-Hygiene
    Write-Host "AUDIT $round/5 HYGIENE PASS"
}

Write-Host "20/20 adversarial audit passes completed."
