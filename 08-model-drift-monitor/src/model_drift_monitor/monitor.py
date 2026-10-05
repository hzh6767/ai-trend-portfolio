"""Feature distribution drift calculations without third-party dependencies."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Mapping, Sequence
from typing import Any

_EPSILON = 1e-12


@dataclass(frozen=True)
class DriftMetric:
    feature: str
    kind: str
    score: float
    threshold: float
    status: str
    details: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "feature": self.feature,
            "kind": self.kind,
            "score": round(self.score, 8),
            "threshold": self.threshold,
            "status": self.status,
            "details": self.details,
        }


@dataclass(frozen=True)
class DriftReport:
    metrics: tuple[DriftMetric, ...]

    @property
    def drifted(self) -> tuple[str, ...]:
        return tuple(metric.feature for metric in self.metrics if metric.status == "drift")

    def as_dict(self) -> dict[str, Any]:
        return {"drifted": list(self.drifted), "metrics": [metric.as_dict() for metric in self.metrics]}


def _is_numeric(values: Sequence[Any]) -> bool:
    return bool(values) and all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values)


def _histogram(values: Sequence[float], edges: Sequence[float]) -> list[int]:
    counts = [0] * (len(edges) - 1)
    for value in values:
        index = 0
        while index < len(edges) - 2 and value >= edges[index + 1]:
            index += 1
        counts[index] += 1
    return counts


def _psi(baseline: Sequence[int], current: Sequence[int]) -> float:
    base_total, current_total = sum(baseline), sum(current)
    score = 0.0
    for base_count, current_count in zip(baseline, current):
        base_rate = max(base_count / base_total, _EPSILON)
        current_rate = max(current_count / current_total, _EPSILON)
        score += (current_rate - base_rate) * math.log(current_rate / base_rate)
    return score


def _numeric_metric(feature: str, baseline: Sequence[float], current: Sequence[float], threshold: float, bins: int) -> DriftMetric:
    low, high = min(baseline), max(baseline)
    if low == high:
        # A constant baseline collapses to one bin; widen the range with the
        # current window so a shifted population can still register as drift.
        low = min(low, min(current))
        high = max(high, max(current))
    if low == high:
        edges = [low - 0.5, high + 0.5]
    else:
        width = (high - low) / bins
        edges = [low + width * index for index in range(bins)] + [high]
    base_counts = _histogram(baseline, edges)
    current_counts = _histogram(current, edges)
    score = _psi(base_counts, current_counts)
    return DriftMetric(feature, "numeric", score, threshold, "drift" if score >= threshold else "ok", {"baseline_counts": base_counts, "current_counts": current_counts})


def _categorical_metric(feature: str, baseline: Sequence[Any], current: Sequence[Any], threshold: float) -> DriftMetric:
    categories = sorted(set(baseline) | set(current), key=lambda value: (type(value).__name__, repr(value)))
    base_total, current_total = len(baseline), len(current)
    base_probs = {category: baseline.count(category) / base_total for category in categories}
    current_probs = {category: current.count(category) / current_total for category in categories}
    score = 0.0
    for category in categories:
        midpoint = (base_probs[category] + current_probs[category]) / 2
        if midpoint:
            if base_probs[category]:
                score += 0.5 * base_probs[category] * math.log(base_probs[category] / midpoint)
            if current_probs[category]:
                score += 0.5 * current_probs[category] * math.log(current_probs[category] / midpoint)
    details = {"categories": [repr(category) for category in categories], "baseline_counts": [baseline.count(category) for category in categories], "current_counts": [current.count(category) for category in categories]}
    return DriftMetric(feature, "categorical", score, threshold, "drift" if score >= threshold else "ok", details)


def monitor(
    baseline: Mapping[str, Sequence[Any]],
    current: Mapping[str, Sequence[Any]],
    *,
    thresholds: Mapping[str, float] | None = None,
    bins: int = 10,
) -> DriftReport:
    """Compare same-named feature collections and return deterministic metrics."""
    if bins < 2:
        raise ValueError("bins must be at least 2")
    if set(baseline) != set(current):
        missing = sorted(set(baseline) - set(current))
        extra = sorted(set(current) - set(baseline))
        raise ValueError(f"feature keys differ (missing={missing}, extra={extra})")
    thresholds = thresholds or {}
    metrics: list[DriftMetric] = []
    for feature in sorted(baseline):
        base_values, current_values = list(baseline[feature]), list(current[feature])
        if not base_values or not current_values:
            raise ValueError(f"feature {feature!r} must have non-empty baseline and current values")
        if _is_numeric(base_values) != _is_numeric(current_values):
            raise ValueError(f"feature {feature!r} changes type between windows")
        threshold = thresholds.get(feature, 0.2)
        if threshold < 0:
            raise ValueError("thresholds must be non-negative")
        if _is_numeric(base_values):
            metrics.append(_numeric_metric(feature, base_values, current_values, threshold, bins))
        else:
            metrics.append(_categorical_metric(feature, base_values, current_values, threshold))
    return DriftReport(tuple(metrics))
