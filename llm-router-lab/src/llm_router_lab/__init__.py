"""Deterministic local model-routing primitives."""

from .router import (
    Endpoint,
    NoRouteAvailable,
    RouteDecision,
    RouteRequest,
    Router,
)

__all__ = ["Endpoint", "NoRouteAvailable", "RouteDecision", "RouteRequest", "Router"]

