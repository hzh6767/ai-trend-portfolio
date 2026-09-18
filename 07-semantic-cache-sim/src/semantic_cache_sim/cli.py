from __future__ import annotations

import argparse
import json

from .cache import SemanticCache


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a deterministic semantic cache demo")
    parser.add_argument("--demo", action="store_true", help="use the built-in cache entries")
    parser.add_argument("--query", default="How do I reset my password?")
    parser.add_argument("--threshold", type=float, default=0.55)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    cache = SemanticCache[str](max_entries=2, similarity_threshold=args.threshold)
    cache.put("How can I reset my password?", "Open Settings > Security and choose Reset password.")
    cache.put("Where can I download invoices?", "Invoices are available under Billing.")
    result = {"query": args.query, "value": cache.get(args.query), "stats": cache.stats().as_dict()}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"query: {result['query']}")
        print(f"value: {result['value']}")
        print(f"stats: {result['stats']}")
    return 0
