from __future__ import annotations

import argparse
import json

from .checker import ToolContract, check_invocation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check an agent tool invocation against a local contract")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--arguments", default='{"path":"reports/today.csv","limit":10}')
    parser.add_argument("--json", action="store_true", help="emit JSON (the default output format)")
    args = parser.parse_args(argv)
    if not args.demo:
        parser.error("--demo is currently the only contract input mode")
    contract = ToolContract("read_report", "Read a report", {"path": {"type": "string", "minLength": 1}, "limit": {"type": "integer", "minimum": 1}}, ("path",))
    try:
        arguments = json.loads(args.arguments)
    except json.JSONDecodeError as exc:
        parser.error(f"invalid --arguments JSON: {exc}")
    print(json.dumps(check_invocation(contract, arguments).as_dict(), indent=2, sort_keys=True))
    return 0
