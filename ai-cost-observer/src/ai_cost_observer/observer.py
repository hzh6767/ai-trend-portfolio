from __future__ import annotations

from collections import defaultdict
from typing import Iterable


DEFAULT_PRICES = {
    "gpt-4o-mini": (0.15, 0.60),
    "claude-3-5-haiku": (0.80, 4.00),
    "gemini-2.0-flash": (0.10, 0.40),
}


def estimate_tokens(text: str) -> int:
    """Provider-neutral upper estimate; never returns zero for non-empty text."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def _token_count(value: object, fallback_text: str) -> int:
    """Use an explicit token count when provided, otherwise estimate from text."""
    if value is None:
        return estimate_tokens(fallback_text)
    return int(value)


def _price(model: str, prices: dict[str, tuple[float, float]]) -> tuple[float, float]:
    if model not in prices:
        raise ValueError(f"unknown model price: {model}")
    return prices[model]


def summarize(records: Iterable[dict], *, budget: float | None = None, prices: dict[str, tuple[float, float]] | None = None) -> dict:
    table = prices or DEFAULT_PRICES
    total = 0.0
    calls = 0
    by_model: dict[str, dict[str, float | int]] = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0.0})
    for record in records:
        model = str(record.get("model") or "")
        prompt = str(record.get("prompt") or "")
        completion = str(record.get("completion") or "")
        input_tokens = _token_count(record.get("input_tokens"), prompt)
        output_tokens = _token_count(record.get("output_tokens"), completion)
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("token counts must be non-negative")
        in_rate, out_rate = _price(model, table)
        cost = input_tokens * in_rate / 1_000_000 + output_tokens * out_rate / 1_000_000
        calls += 1
        total += cost
        item = by_model[model]
        item["calls"] += 1
        item["tokens"] += input_tokens + output_tokens
        item["cost"] += cost
    result = {"calls": calls, "total_cost": round(total, 8), "by_model": dict(by_model)}
    if budget is not None:
        result["budget"] = budget
        result["within_budget"] = total <= budget
        result["remaining"] = round(budget - total, 8)
    return result
