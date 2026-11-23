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

    def test_invalid_counts_are_not_rounded_or_coerced(self):
        for value in (0.9, -0.9, True, False, [], float("inf")):
            for field in ("input_tokens", "output_tokens"):
                with self.subTest(value=value, field=field), self.assertRaises(ValueError):
                    summarize([{"model": "gpt-4o-mini", field: value}])

    def test_whole_number_inputs_remain_compatible(self):
        result = summarize([{"model": "gpt-4o-mini", "input_tokens": "2", "output_tokens": 3.0}])
        self.assertEqual(result["by_model"]["gpt-4o-mini"]["tokens"], 5)

    def test_empty_price_table_is_respected(self):
        with self.assertRaisesRegex(ValueError, "unknown model"):
            summarize([{"model": "gpt-4o-mini"}], prices={})

    def test_non_object_record_is_reported(self):
        with self.assertRaisesRegex(ValueError, "JSON object"):
            summarize([[]])

    def test_null_token_fields_fall_back_to_estimate(self):
        result = summarize([
            {"model": "gpt-4o-mini", "prompt": "abcd", "completion": "abcd", "input_tokens": None, "output_tokens": None}
        ])
        self.assertEqual(result["calls"], 1)
        self.assertGreater(result["by_model"]["gpt-4o-mini"]["tokens"], 0)


if __name__ == "__main__":
    unittest.main()
