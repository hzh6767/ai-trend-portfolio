from __future__ import annotations

from collections import Counter
from typing import Iterable


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    index = min(len(values) - 1, max(0, int(round((len(values) - 1) * fraction))))
    return round(values[index], 3)


def analyze(records: Iterable[dict]) -> dict:
    durations: list[float] = []
    errors = 0
    events = 0
    tools: Counter[str] = Counter()
    traces: Counter[str] = Counter()
    for record in records:
        events += 1
        try:
            duration = float(record["ended_at_ms"]) - float(record["started_at_ms"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("each event needs numeric started_at_ms and ended_at_ms") from exc
        if duration < 0:
            raise ValueError("ended_at_ms cannot precede started_at_ms")
        durations.append(duration)
        trace_id = str(record.get("trace_id", ""))
        if trace_id:
            traces[trace_id] += 1
        if str(record.get("status", "")).lower() in {"error", "failed", "failure"}:
            errors += 1
        if record.get("event") == "tool_call" or record.get("tool"):
            tools[str(record.get("tool", "unknown"))] += 1
    result = {
        "events": events,
        "traces": len(traces),
        "error_rate": round(errors / events, 4) if events else 0.0,
        "latency_ms": {"p50": _percentile(durations, 0.50), "p95": _percentile(durations, 0.95), "max": max(durations, default=0.0)},
        "tool_calls": sum(tools.values()),
        "tools": dict(tools),
    }
    return result
