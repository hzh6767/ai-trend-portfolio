import unittest

from ai_cost_observer import estimate_tokens, summarize


class ObserverTests(unittest.TestCase):
    def test_estimate_is_nonzero_for_nonempty_text(self):
        self.assertEqual(estimate_tokens("abcd"), 1)
        self.assertEqual(estimate_tokens(""), 0)

    def test_budget_summary(self):
        result = summarize([{"model": "gpt-4o-mini", "prompt": "abcd", "completion": "abcd"}], budget=1)
        self.assertEqual(result["calls"], 1)
        self.assertTrue(result["within_budget"])

    def test_unknown_model_is_explicit(self):
        with self.assertRaisesRegex(ValueError, "unknown model"):
            summarize([{"model": "unknown", "prompt": "x"}])


if __name__ == "__main__":
    unittest.main()
