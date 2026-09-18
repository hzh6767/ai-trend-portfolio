from __future__ import annotations

import argparse
import json

from .monitor import monitor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare offline baseline/current feature distributions")
    parser.add_argument("--demo", action="store_true", help="run built-in distributions")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.demo:
        parser.error("--demo is currently the only input mode")
    report = monitor(
        {"latency_ms": [100, 110, 105, 95, 120, 100], "region": ["us", "us", "eu", "us", "eu", "us"]},
        {"latency_ms": [102, 108, 111, 107, 105, 109], "region": ["apac", "apac", "us", "apac", "us", "apac"]},
        thresholds={"latency_ms": 0.1, "region": 0.05},
    )
    if args.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        for metric in report.metrics:
            print(f"{metric.feature}: {metric.status} score={metric.score:.4f} threshold={metric.threshold:.4f}")
    return 0
