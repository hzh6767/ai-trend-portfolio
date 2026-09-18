# Agent Trace Analyzer

A dependency-free analyzer for JSONL traces from LLM agents. It computes latency percentiles, error rate, tool-call loops, and the slowest operations so agentic workflows can be reviewed before deployment.

Each record should include `trace_id`, `event`, `started_at_ms`, `ended_at_ms`, and optional `status` / `tool`. Timestamps are numeric milliseconds.

```powershell
python -m agent_trace_analyzer --input traces.jsonl
```

## Development

```powershell
python -m unittest discover -s tests -v
```
