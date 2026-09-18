"""Deterministic retrieval-augmented generation evaluation helpers."""

from .evaluator import (
    EvaluationCase,
    EvaluationResult,
    EvidenceDocument,
    evaluate_case,
    token_f1,
)

__all__ = [
    "EvaluationCase",
    "EvaluationResult",
    "EvidenceDocument",
    "evaluate_case",
    "token_f1",
]

