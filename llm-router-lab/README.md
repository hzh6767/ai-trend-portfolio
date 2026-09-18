# llm-router-lab

An offline model-routing laboratory for applications that need predictable
fallbacks across multiple LLM endpoints. It chooses a healthy endpoint by
context capacity, capability, cost, latency, quality floor, and routing
strategy. No provider SDKs, network calls, credentials, or wall-clock health
checks are required.

## Quick start

```text
python -m unittest discover -s tests -v
python -m pip install -e .
python -m llm_router_lab --demo
python -m llm_router_lab --input-tokens 1200 --max-output-tokens 300 --strategy cost --json
```

After `python -m pip install -e .`, the console command is `llm-route`.

## Routing behavior

An endpoint is eligible only when it is healthy, supports every requested
capability, has enough context for input plus output tokens, meets the optional
cost and latency budgets, and clears the quality floor. Eligible endpoints are
ranked deterministically by a weighted score:

* `balanced`: quality, cost, and latency receive balanced weights;
* `cost`: cost dominates while preserving quality and latency;
* `latency`: p95 latency dominates;
* `quality`: the endpoint quality estimate dominates.

Ties break by model ID, so the same input gives the same decision. Rejections
are returned with reasons to make fallback behavior observable. The router
also exposes explicit `mark_failure`, `mark_success`, and `set_health` methods
for an application's health-check loop; it does not make hidden network calls.

The included quality value is a local routing hint, not a benchmark claim.
Replace it with measurements from your own evaluation pipeline.

## Layout

```text
src/llm_router_lab/  router library and CLI
tests/               stdlib unittest coverage
```
