from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .redactor import findings_as_dicts, redact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Redact common PII and secret-shaped values offline")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--file", type=Path)
    args = parser.parse_args(argv)
    try:
        text = args.text if args.text is not None else args.file.read_text(encoding="utf-8")
        redacted, findings = redact(text)
    except OSError as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    print(json.dumps({"redacted": redacted, "findings": findings_as_dicts(findings), "count": len(findings)}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
