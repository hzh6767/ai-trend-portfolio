"""Command-line demo for the local model router."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .router import Endpoint, RouteRequest, Router


def demo_router() -> Router:
    return Router(
        [
            Endpoint("fast-small", "local", 0.20, 180, 8192, frozenset({"chat", "json"}), 0.76),
            Endpoint("balanced-mid", "local", 0.70, 420, 32768, frozenset({"chat", "json", "tools"}), 0.90),
            Endpoint("quality-large", "local", 1.80, 900, 131072, frozenset({"chat", "json", "tools"}), 0.97),
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Route a request across local model metadata")
    parser.add_argument("--demo", action="store_true", help="use built-in endpoints")
    parser.add_argument("--input-tokens", type=int, default=1000)
    parser.add_argument("--max-output-tokens", type=int, default=256)
    parser.add_argument("--capability", action="append", default=[])
    parser.add_argument("--max-cost", type=float)
    parser.add_argument("--max-latency-ms", type=int)
    parser.add_argument("--min-quality", type=float, default=0.0)
    parser.add_argument("--strategy", choices=("balanced", "cost", "latency", "quality"), default="balanced")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    router = demo_router()
    request = RouteRequest(
        args.input_tokens,
        args.max_output_tokens,
        frozenset(args.capability),
        args.max_cost,
        args.max_latency_ms,
        args.min_quality,
        args.strategy,
    )
    decision = router.route(request)
    if args.json:
        print(json.dumps(decision.as_dict(), indent=2, sort_keys=True))
    else:
        print(f"selected_model: {decision.selected_model}")
        for candidate in decision.candidates:
            print(f"candidate: {candidate.model_id} score={candidate.score:.3f}")
        for rejection in decision.rejected:
            print(f"rejected: {rejection.model_id} ({', '.join(rejection.reasons)})")
    return 0

