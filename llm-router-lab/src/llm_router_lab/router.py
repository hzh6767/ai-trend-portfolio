"""Offline, deterministic model endpoint selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


_WEIGHTS: Mapping[str, tuple[float, float, float, float]] = {
    # quality, cost, latency, context headroom
    "balanced": (0.35, 0.25, 0.25, 0.15),
    "cost": (0.20, 0.55, 0.15, 0.10),
    "latency": (0.20, 0.15, 0.55, 0.10),
    "quality": (0.65, 0.10, 0.15, 0.10),
}


@dataclass(frozen=True)
class Endpoint:
    """Static metadata for one model endpoint."""

    model_id: str
    provider: str
    cost_per_1k_tokens: float
    p95_latency_ms: int
    context_window: int
    capabilities: frozenset[str] = frozenset()
    quality: float = 0.5
    healthy: bool = True

    def __post_init__(self) -> None:
        if not self.model_id.strip():
            raise ValueError("model_id must not be empty")
        if self.cost_per_1k_tokens < 0:
            raise ValueError("cost_per_1k_tokens must be non-negative")
        if self.p95_latency_ms <= 0 or self.context_window <= 0:
            raise ValueError("latency and context_window must be positive")
        if not 0 <= self.quality <= 1:
            raise ValueError("quality must be in [0, 1]")


@dataclass(frozen=True)
class RouteRequest:
    """Constraints and preferences for one route decision."""

    input_tokens: int
    max_output_tokens: int
    required_capabilities: frozenset[str] = frozenset()
    max_cost: float | None = None
    max_latency_ms: int | None = None
    min_quality: float = 0.0
    strategy: str = "balanced"

    def __post_init__(self) -> None:
        if self.input_tokens < 0 or self.max_output_tokens < 0:
            raise ValueError("token counts must be non-negative")
        if self.max_cost is not None and self.max_cost < 0:
            raise ValueError("max_cost must be non-negative")
        if self.max_latency_ms is not None and self.max_latency_ms <= 0:
            raise ValueError("max_latency_ms must be positive")
        if not 0 <= self.min_quality <= 1:
            raise ValueError("min_quality must be in [0, 1]")
        if self.strategy not in _WEIGHTS:
            raise ValueError(f"strategy must be one of {', '.join(_WEIGHTS)}")

    @property
    def required_context(self) -> int:
        return self.input_tokens + self.max_output_tokens


@dataclass(frozen=True)
class CandidateScore:
    model_id: str
    score: float
    quality_component: float
    cost_component: float
    latency_component: float
    context_component: float

    def as_dict(self) -> dict[str, object]:
        return {
            "model_id": self.model_id,
            "score": round(self.score, 6),
            "components": {
                "quality": round(self.quality_component, 6),
                "cost": round(self.cost_component, 6),
                "latency": round(self.latency_component, 6),
                "context": round(self.context_component, 6),
            },
        }


@dataclass(frozen=True)
class Rejection:
    model_id: str
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {"model_id": self.model_id, "reasons": list(self.reasons)}


@dataclass(frozen=True)
class RouteDecision:
    selected_model: str
    candidates: tuple[CandidateScore, ...]
    rejected: tuple[Rejection, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "selected_model": self.selected_model,
            "candidates": [candidate.as_dict() for candidate in self.candidates],
            "rejected": [rejection.as_dict() for rejection in self.rejected],
        }


class NoRouteAvailable(RuntimeError):
    """Raised when every endpoint fails at least one request constraint."""

    def __init__(self, rejected: tuple[Rejection, ...]) -> None:
        self.rejected = rejected
        detail = "; ".join(f"{item.model_id}: {', '.join(item.reasons)}" for item in rejected)
        super().__init__(f"no endpoint satisfies request ({detail})")


@dataclass
class _Health:
    healthy: bool
    consecutive_failures: int = 0


class Router:
    """Select endpoints with explicit, mutable health state.

    Health state starts from each endpoint's ``healthy`` field. The router only
    changes state when an application explicitly calls a health method.
    """

    def __init__(self, endpoints: Iterable[Endpoint], failure_threshold: int = 2) -> None:
        self._endpoints = tuple(endpoints)
        if not self._endpoints:
            raise ValueError("at least one endpoint is required")
        ids = [endpoint.model_id for endpoint in self._endpoints]
        if len(ids) != len(set(ids)):
            raise ValueError("endpoint model_id values must be unique")
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be positive")
        self._failure_threshold = failure_threshold
        self._health = {endpoint.model_id: _Health(endpoint.healthy) for endpoint in self._endpoints}

    @property
    def endpoints(self) -> tuple[Endpoint, ...]:
        return self._endpoints

    def set_health(self, model_id: str, healthy: bool) -> None:
        self._health_for(model_id).healthy = bool(healthy)
        if healthy:
            self._health_for(model_id).consecutive_failures = 0

    def mark_failure(self, model_id: str) -> None:
        state = self._health_for(model_id)
        state.consecutive_failures += 1
        if state.consecutive_failures >= self._failure_threshold:
            state.healthy = False

    def mark_success(self, model_id: str) -> None:
        state = self._health_for(model_id)
        state.consecutive_failures = 0
        state.healthy = True

    def health_snapshot(self) -> dict[str, bool]:
        return {model_id: state.healthy for model_id, state in self._health.items()}

    def _health_for(self, model_id: str) -> _Health:
        try:
            return self._health[model_id]
        except KeyError as exc:
            raise KeyError(f"unknown model_id: {model_id}") from exc

    @staticmethod
    def _component(value: float, maximum: float) -> float:
        if maximum <= 0:
            return 1.0
        return max(0.0, min(1.0, 1.0 - value / maximum))

    def route(self, request: RouteRequest) -> RouteDecision:
        """Return the highest-scoring eligible endpoint or raise a clear error."""

        eligible: list[Endpoint] = []
        rejected: list[Rejection] = []
        for endpoint in self._endpoints:
            reasons: list[str] = []
            if not self._health[endpoint.model_id].healthy:
                reasons.append("unhealthy")
            if endpoint.context_window < request.required_context:
                reasons.append("insufficient_context")
            missing = request.required_capabilities - endpoint.capabilities
            if missing:
                reasons.append("missing_capability:" + ",".join(sorted(missing)))
            estimated_cost = endpoint.cost_per_1k_tokens * request.required_context / 1000
            if request.max_cost is not None and estimated_cost > request.max_cost:
                reasons.append("cost_budget")
            if request.max_latency_ms is not None and endpoint.p95_latency_ms > request.max_latency_ms:
                reasons.append("latency_budget")
            if endpoint.quality < request.min_quality:
                reasons.append("quality_floor")
            if reasons:
                rejected.append(Rejection(endpoint.model_id, tuple(reasons)))
            else:
                eligible.append(endpoint)
        if not eligible:
            raise NoRouteAvailable(tuple(rejected))

        max_cost = max(endpoint.cost_per_1k_tokens for endpoint in eligible)
        max_latency = max(endpoint.p95_latency_ms for endpoint in eligible)
        max_context = max(endpoint.context_window for endpoint in eligible)
        weights = _WEIGHTS[request.strategy]
        scores: list[CandidateScore] = []
        for endpoint in eligible:
            quality = endpoint.quality
            cost = self._component(endpoint.cost_per_1k_tokens, max_cost)
            latency = self._component(endpoint.p95_latency_ms, max_latency)
            context = max(0.0, min(1.0, endpoint.context_window / max_context))
            score = weights[0] * quality + weights[1] * cost + weights[2] * latency + weights[3] * context
            scores.append(CandidateScore(endpoint.model_id, score, quality, cost, latency, context))
        scores.sort(key=lambda item: (-item.score, item.model_id))
        return RouteDecision(scores[0].model_id, tuple(scores), tuple(rejected))

