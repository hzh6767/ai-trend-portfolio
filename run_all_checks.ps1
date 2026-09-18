param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$projects = @(
    @{ Directory = "rag-eval-kit"; Package = "rag_eval_kit"; Demo = @("--demo", "--json") },
    @{ Directory = "prompt-injection-firewall"; Package = "prompt_injection_firewall"; Demo = @("--demo", "--json"); ExpectedExit = 2 },
    @{ Directory = "llm-router-lab"; Package = "llm_router_lab"; Demo = @("--demo", "--json") },
    @{ Directory = "structured-output-guard"; Package = "structured_output_guard"; Demo = @() },
    @{ Directory = "ai-cost-observer"; Package = "ai_cost_observer"; Demo = @() },
    @{ Directory = "agent-trace-analyzer"; Package = "agent_trace_analyzer"; Demo = @() },
    @{ Directory = "pii-redactor"; Package = "pii_redactor"; Demo = @() },
    @{ Directory = "07-semantic-cache-sim"; Package = "semantic_cache_sim"; Demo = @("--demo") },
    @{ Directory = "08-model-drift-monitor"; Package = "model_drift_monitor"; Demo = @("--demo") },
    @{ Directory = "09-tool-contract-checker"; Package = "tool_contract_checker"; Demo = @("--demo") }
)

foreach ($project in $projects) {
    $directory = Join-Path $PSScriptRoot $project.Directory
    Write-Host "== $($project.Directory) =="
    $env:PYTHONPATH = Join-Path $directory "src"
    & $Python -m unittest discover -s (Join-Path $directory "tests") -v
    if ($LASTEXITCODE -ne 0) { throw "Tests failed: $($project.Directory)" }
    & $Python -m compileall -q (Join-Path $directory "src") (Join-Path $directory "tests")
    if ($LASTEXITCODE -ne 0) { throw "Compile failed: $($project.Directory)" }
    if ($project.Demo.Count -gt 0) {
        & $Python -m $project.Package @($project.Demo)
        $expectedExit = if ($project.ContainsKey("ExpectedExit")) { $project.ExpectedExit } else { 0 }
        if ($LASTEXITCODE -ne $expectedExit) { throw "Demo failed: $($project.Directory), expected exit $expectedExit, got $LASTEXITCODE" }
    }
}

Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
Write-Host "All project checks passed."
