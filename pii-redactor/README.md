# PII Redactor

An offline, explainable redaction pipeline for AI prompts, traces, and logs. It masks emails, phone numbers, IP addresses, credit-card-like numbers, bearer tokens, and common API-key shapes before data enters an LLM observability or evaluation workflow.

The scanner returns structured findings with positions and replacement counts. It never sends text over the network and does not attempt to validate whether a secret is live.

```powershell
$env:PYTHONPATH = "src"
python -m pii_redactor --text "Contact alice@example.com with Bearer abc.def.ghi"
```

## Development

```powershell
python -m unittest discover -s tests -v
```
