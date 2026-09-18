import unittest

from agent_trace_analyzer import analyze


class AnalyzerTests(unittest.TestCase):
    def test_summary(self):
        result = analyze([
            {"trace_id": "a", "event": "model", "started_at_ms": 0, "ended_at_ms": 10, "status": "ok"},
            {"trace_id": "a", "event": "tool_call", "tool": "search", "started_at_ms": 10, "ended_at_ms": 30, "status": "error"},
        ])
        self.assertEqual(result["traces"], 1)
        self.assertEqual(result["tool_calls"], 1)
        self.assertEqual(result["error_rate"], 0.5)

    def test_negative_duration_is_rejected(self):
        with self.assertRaises(ValueError):
            analyze([{"started_at_ms": 2, "ended_at_ms": 1}])


if __name__ == "__main__":
    unittest.main()
