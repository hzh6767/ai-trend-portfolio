from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analyzer import analyze


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze JSONL LLM agent traces")
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        records = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
        result = analyze(records)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
