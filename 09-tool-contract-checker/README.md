# Tool Contract Checker

`tool-contract-checker` validates a small JSON-compatible tool contract before an agent is allowed to invoke it. It checks required and unknown parameters, primitive types, enums and bounds, then reports high-signal safety warnings for path traversal and shell-like argument values. It is deterministic and stdlib-only.

```powershell
python -m tool_contract_checker --demo
python -m unittest discover -s tests -v
```

The checker does not execute tools. Treat its result as a gate before dispatching to a real tool runner, and keep the contract as the single source of truth for the tool's argument shape.
