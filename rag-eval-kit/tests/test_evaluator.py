import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_eval_kit import EvaluationCase, EvidenceDocument, evaluate_case, token_f1


class EvaluatorTests(unittest.TestCase):
    def test_token_f1_is_case_insensitive(self):
        self.assertEqual(token_f1("A quick test", "a QUICK test"), 1.0)

    def test_empty_token_f1_is_defined(self):
        self.assertEqual(token_f1("", ""), 1.0)
        self.assertEqual(token_f1("", "word"), 0.0)

    def test_context_and_citation_metrics(self):
        case = EvaluationCase.from_values(
            "refund window",
            "Refunds are available within 30 days.",
            [
                EvidenceDocument("policy", "Refunds are available within 30 days."),
                EvidenceDocument("noise", "Support is available by email."),
            ],
            citations=["policy"],
            relevant_document_ids=["policy"],
            reference_citations=["policy"],
        )
        result = evaluate_case(case)
        self.assertEqual(result.metrics["context_recall"], 1.0)
        self.assertEqual(result.metrics["citation_precision"], 1.0)
        self.assertEqual(result.metrics["citation_recall"], 1.0)

    def test_unknown_citation_is_not_supported(self):
        case = EvaluationCase.from_values(
            "question", "An answer.", [EvidenceDocument("doc", "Evidence.")], citations=["missing"]
        )
        self.assertEqual(evaluate_case(case).metrics["citation_precision"], 0.0)

    def test_empty_context_has_zero_grounding(self):
        case = EvaluationCase.from_values("q", "A claim.", [])
        result = evaluate_case(case)
        self.assertEqual(result.metrics["grounding"], 0.0)
        self.assertTrue(result.findings)

    def test_cli_demo_emits_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "rag_eval_kit", "--demo", "--json"],
            cwd=ROOT,
            env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        self.assertIn("grounding", payload["metrics"])


if __name__ == "__main__":
    unittest.main()

