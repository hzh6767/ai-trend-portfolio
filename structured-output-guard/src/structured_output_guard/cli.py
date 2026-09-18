from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .validator import ValidationError, extract_json, validate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate LLM JSON against a small deterministic schema")
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--response", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        schema = json.loads(args.schema.read_text(encoding="utf-8"))
        value = validate(extract_json(args.response.read_text(encoding="utf-8")), schema)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"valid": True, "value": value}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
