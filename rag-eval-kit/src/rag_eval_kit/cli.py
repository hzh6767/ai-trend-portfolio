"""Command-line interface for the local RAG evaluator."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .evaluator import EvaluationCase, EvidenceDocument, evaluate_case


def _context(value: str) -> EvidenceDocument:
    document_id, separator, text = value.partition("::")
    if not separator or not document_id.strip() or not text.strip():
        raise argparse.ArgumentTypeError("context must use ID::TEXT")
    return EvidenceDocument(document_id.strip(), text.strip())


def _demo() -> EvaluationCase:
    return EvaluationCase.from_values(
        query="refund window",
        answer="Refunds are available within 30 days of purchase.",
        retrieved=[
            EvidenceDocument("policy", "Refunds are available within 30 days of purchase."),
            EvidenceDocument("pricing", "Annual plans include priority support."),
        ],
        citations=["policy"],
        relevant_document_ids=["policy"],
        reference_citations=["policy"],
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate a RAG answer without network calls")
    parser.add_argument("--demo", action="store_true", help="run the built-in example")
    parser.add_argument("--query", help="user query")
    parser.add_argument("--answer", help="generated answer")
    parser.add_argument("--context", action="append", type=_context, default=[], metavar="ID::TEXT")
    parser.add_argument("--citation", action="append", default=[])
    parser.add_argument("--relevant-id", action="append", default=[])
    parser.add_argument("--reference-citation", action="append", default=[])
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.demo:
        case = _demo()
    else:
        if args.query is None or args.answer is None:
            raise SystemExit("--query and --answer are required unless --demo is used")
        case = EvaluationCase.from_values(
            args.query,
            args.answer,
            args.context,
            args.citation,
            args.relevant_id,
            args.reference_citation,
        )
    result = evaluate_case(case)
    if args.json:
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        for name, value in result.metrics.items():
            print(f"{name}: {value:.3f}")
        for finding in result.findings:
            print(f"finding: {finding}")
    return 0
