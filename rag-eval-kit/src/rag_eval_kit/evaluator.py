"""Offline RAG metrics based on normalized token overlap.

The module deliberately avoids probabilistic or network-backed judges. It is
useful as a fast lower-bound signal in tests and local evaluation pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Mapping, Sequence


_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_SENTENCE_RE = re.compile(r"[^.!?\n]+(?:[.!?]+|$)")


def _tokens(text: str) -> frozenset[str]:
    return frozenset(token.casefold() for token in _TOKEN_RE.findall(text or ""))


def token_f1(left: str, right: str) -> float:
    """Return set-based token F1 for two strings, always in ``[0, 1]``."""

    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = len(left_tokens & right_tokens)
    precision = overlap / len(left_tokens)
    recall = overlap / len(right_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


@dataclass(frozen=True)
class EvidenceDocument:
    """A retrieved or reference document with a stable identifier."""

    document_id: str
    text: str

    def __post_init__(self) -> None:
        if not self.document_id.strip():
            raise ValueError("document_id must not be empty")


@dataclass(frozen=True)
class EvaluationCase:
    """Inputs for one deterministic RAG evaluation."""

    query: str
    answer: str
    retrieved: tuple[EvidenceDocument, ...]
    citations: tuple[str, ...] = ()
    relevant_document_ids: frozenset[str] = frozenset()
    reference_citations: frozenset[str] = frozenset()

    @classmethod
    def from_values(
        cls,
        query: str,
        answer: str,
        retrieved: Iterable[EvidenceDocument],
        citations: Iterable[str] = (),
        relevant_document_ids: Iterable[str] = (),
        reference_citations: Iterable[str] = (),
    ) -> "EvaluationCase":
        return cls(
            query=query,
            answer=answer,
            retrieved=tuple(retrieved),
            citations=tuple(citations),
            relevant_document_ids=frozenset(relevant_document_ids),
            reference_citations=frozenset(reference_citations),
        )


@dataclass(frozen=True)
class EvaluationResult:
    """Metric values plus human-readable, deterministic findings."""

    metrics: Mapping[str, float]
    findings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {"metrics": dict(self.metrics), "findings": list(self.findings)}


def _unique_ids(values: Iterable[str]) -> set[str]:
    return {value.strip() for value in values if value and value.strip()}


def _context_metrics(case: EvaluationCase) -> tuple[float, float]:
    retrieved_ids = {document.document_id for document in case.retrieved}
    if case.relevant_document_ids:
        relevant = retrieved_ids & set(case.relevant_document_ids)
    else:
        query_tokens = _tokens(case.query)
        relevant = {
            document.document_id
            for document in case.retrieved
            if query_tokens & _tokens(document.text)
        }
    precision = len(relevant) / len(retrieved_ids) if retrieved_ids else 0.0
    if case.relevant_document_ids:
        recall = len(relevant) / len(case.relevant_document_ids)
    else:
        recall = precision
    return precision, recall


def _citation_metrics(case: EvaluationCase) -> tuple[float, float]:
    cited = _unique_ids(case.citations)
    documents: dict[str, EvidenceDocument] = {}
    for document in case.retrieved:
        documents.setdefault(document.document_id, document)
    valid_citations = {
        document_id
        for document_id in cited
        if document_id in documents
        and any(token_f1(sentence, documents[document_id].text) >= 0.15 for sentence in _sentences(case.answer))
    }
    precision = len(valid_citations) / len(cited) if cited else 0.0
    if case.reference_citations:
        recall = len(cited & set(case.reference_citations)) / len(case.reference_citations)
    else:
        recall = 0.0
    return precision, recall


def _sentences(answer: str) -> tuple[str, ...]:
    return tuple(match.group(0).strip() for match in _SENTENCE_RE.finditer(answer or "") if match.group(0).strip())


def _grounding(case: EvaluationCase) -> float:
    sentences = _sentences(case.answer)
    if not sentences or not case.retrieved:
        return 0.0
    return sum(
        max(token_f1(sentence, document.text) for document in case.retrieved)
        for sentence in sentences
    ) / len(sentences)


def evaluate_case(case: EvaluationCase) -> EvaluationResult:
    """Evaluate one case and return five stable metrics.

    Duplicate document IDs are counted once for precision/recall, while the
    first occurrence is used as evidence. This avoids inflating a score by
    repeating the same citation.
    """

    context_precision, context_recall = _context_metrics(case)
    citation_precision, citation_recall = _citation_metrics(case)
    metrics = {
        "context_precision": round(context_precision, 6),
        "context_recall": round(context_recall, 6),
        "citation_precision": round(citation_precision, 6),
        "citation_recall": round(citation_recall, 6),
        "grounding": round(_grounding(case), 6),
    }
    findings: list[str] = []
    if metrics["context_precision"] < 0.5:
        findings.append("retrieved context contains limited query-relevant evidence")
    if metrics["context_recall"] < 1.0 and case.relevant_document_ids:
        findings.append("one or more known relevant documents were not retrieved")
    if metrics["citation_precision"] < 1.0:
        findings.append("at least one citation is missing, unknown, or weakly supported")
    if metrics["grounding"] < 0.5:
        findings.append("answer claims have weak lexical support in retrieved context")
    if not findings:
        findings.append("no threshold findings")
    return EvaluationResult(metrics=metrics, findings=tuple(findings))
