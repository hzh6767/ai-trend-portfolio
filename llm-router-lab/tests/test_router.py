import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from llm_router_lab import Endpoint, NoRouteAvailable, RouteRequest, Router


def make_router() -> Router:
    return Router(
        [
            Endpoint("cheap", "test", 0.10, 600, 8192, frozenset({"chat"}), 0.70),
            Endpoint("fast", "test", 0.50, 100, 8192, frozenset({"chat", "json"}), 0.80),
            Endpoint("large", "test", 1.50, 900, 131072, frozenset({"chat", "json", "tools"}), 0.98),
        ]
    )


class RouterTests(unittest.TestCase):
    def test_latency_strategy_prefers_fast_endpoint(self):
        decision = make_router().route(RouteRequest(100, 100, strategy="latency"))
        self.assertEqual(decision.selected_model, "fast")

    def test_cost_budget_filters_expensive_endpoint(self):
        decision = make_router().route(RouteRequest(1000, 1000, max_cost=0.25, strategy="cost"))
        self.assertEqual(decision.selected_model, "cheap")
        rejected = {item.model_id: item for item in decision.rejected}
        self.assertIn("cost_budget", rejected["large"].reasons)

    def test_capability_and_context_constraints_are_reported(self):
        decision = make_router().route(RouteRequest(100, 100, frozenset({"tools"})))
        self.assertEqual(decision.selected_model, "large")
        self.assertTrue(any("missing_capability:tools" in item.reasons for item in decision.rejected))

    def test_unhealthy_endpoints_are_skipped(self):
        router = make_router()
        router.set_health("fast", False)
        decision = router.route(RouteRequest(100, 100, strategy="latency"))
        self.assertNotEqual(decision.selected_model, "fast")
        self.assertIn("unhealthy", next(item for item in decision.rejected if item.model_id == "fast").reasons)

    def test_failure_threshold_and_success_recovery(self):
        router = Router([Endpoint("x", "test", 1, 100, 1000)], failure_threshold=2)
        router.mark_failure("x")
        self.assertTrue(router.health_snapshot()["x"])
        router.mark_failure("x")
        self.assertFalse(router.health_snapshot()["x"])
        router.mark_success("x")
        self.assertTrue(router.health_snapshot()["x"])

    def test_no_route_raises_with_reasons(self):
        router = make_router()
        with self.assertRaises(NoRouteAvailable) as caught:
            router.route(RouteRequest(100, 100, frozenset({"vision"})))
        self.assertTrue(caught.exception.rejected)
        self.assertTrue(any("missing_capability:vision" in item.reasons for item in caught.exception.rejected))

    def test_cli_demo_emits_json(self):
        completed = subprocess.run(
            [sys.executable, "-m", "llm_router_lab", "--demo", "--json"],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        self.assertIn(payload["selected_model"], {"fast-small", "balanced-mid", "quality-large"})


if __name__ == "__main__":
    unittest.main()

