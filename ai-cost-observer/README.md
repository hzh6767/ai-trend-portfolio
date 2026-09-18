# AI Cost Observer

Offline cost and budget analysis for LLM request logs. It estimates tokens conservatively from characters, applies a versioned model price table, and reports the calls that would exceed a budget. It accepts JSON Lines so it can be used in CI, cron jobs, or a gateway log pipeline.

```powershell
python -m ai_cost_observer --input examples.jsonl --budget 1.00
```

No credentials, network calls, or provider SDKs are required.

## Development

```powershell
python -m unittest discover -s tests -v
```
