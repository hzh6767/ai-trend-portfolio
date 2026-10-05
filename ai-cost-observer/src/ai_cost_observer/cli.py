from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .observer import summarize


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze JSONL LLM logs without contacting a provider")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--budget", type=float)
    args = parser.parse_args(argv)
    try:
        records = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
        result = summarize(records, budget=args.budget)
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("within_budget", True) else 3


if __name__ == "__main__":
    sys.exit(main())
