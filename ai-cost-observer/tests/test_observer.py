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

    def test_null_token_fields_fall_back_to_estimate(self):
        result = summarize([
            {"model": "gpt-4o-mini", "prompt": "abcd", "completion": "abcd", "input_tokens": None, "output_tokens": None}
        ])
        self.assertEqual(result["calls"], 1)
        self.assertGreater(result["by_model"]["gpt-4o-mini"]["tokens"], 0)


if __name__ == "__main__":
    unittest.main()
