# AI Trend Portfolio

Ten small, auditable AI engineering projects focused on the production trends that matter now: agent reliability, RAG evaluation, prompt-injection defense, structured outputs, model routing, cost observability, trace analysis, privacy, semantic caching, drift monitoring, and tool contracts.

Every project is self-contained, uses the Python standard library at runtime, has a CLI, and includes unit tests. No project requires an API key or makes a network request.

## Projects

| Project | Focus |
| --- | --- |
| [`rag-eval-kit`](rag-eval-kit) | Offline RAG retrieval, citation, grounding, and token metrics |
| [`prompt-injection-firewall`](prompt-injection-firewall) | Explainable Unicode-aware prompt-injection and exfiltration rules |
| [`llm-router-lab`](llm-router-lab) | Deterministic routing by capability, health, quality, cost, and latency |
| [`structured-output-guard`](structured-output-guard) | Schema-first validation for model-generated JSON |
| [`ai-cost-observer`](ai-cost-observer) | Offline token, price, and budget analysis for JSONL logs |
| [`agent-trace-analyzer`](agent-trace-analyzer) | Agent latency, error, and tool-call observability |
| [`pii-redactor`](pii-redactor) | Explainable offline redaction for prompts and traces |
| [`07-semantic-cache-sim`](07-semantic-cache-sim) | Deterministic similarity-cache behavior and hit/miss analysis |
| [`08-model-drift-monitor`](08-model-drift-monitor) | Baseline-versus-current quality and latency drift detection |
| [`09-tool-contract-checker`](09-tool-contract-checker) | Validation of tool schemas, arguments, and result contracts |

## Run Everything

From this repository root:

```powershell
.un_all_checks.ps1 -Python python
```

On this workstation the verified interpreter is `E:\anaconda3\python.exe`:

```powershell
.\run_all_checks.ps1 -Python E:\anaconda3\python.exe
```

The script runs each project's tests, bytecode compilation, and deterministic demo where available. A non-zero result stops the run.

## Audit Boundary

The projects are intentionally offline and deterministic. Inputs are treated as untrusted data, malformed records fail closed, and the demos do not contact model providers. This portfolio is a set of focused engineering references, not a hosted service or a claim of model quality.

## License

Each project is released under the MIT License unless its own directory states otherwise.
