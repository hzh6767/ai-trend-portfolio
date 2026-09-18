# Structured Output Guard

Schema-first validation for JSON returned by LLMs. It extracts fenced JSON, rejects malformed or ambiguous output, and validates a small auditable JSON Schema subset without an API key.

```powershell
python -m structured_output_guard --schema schema.json --response response.txt
```

Supported keywords are `type`, `required`, `properties`, `items`, `enum`, and `additionalProperties`. The validator is deliberately deterministic so it can sit between an LLM and an automation pipeline.

## Development

```powershell
python -m unittest discover -s tests -v
```
