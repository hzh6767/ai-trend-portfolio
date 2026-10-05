import unittest

from model_drift_monitor import monitor


class DriftMonitorTests(unittest.TestCase):
    def test_identical_numeric_distribution_is_stable(self):
        report = monitor({"x": [1, 2, 3, 4]}, {"x": [1, 2, 3, 4]})
        self.assertEqual(report.drifted, ())
        self.assertEqual(report.metrics[0].score, 0.0)

    def test_categorical_shift_is_detected(self):
        report = monitor({"color": ["red"] * 8 + ["blue"] * 2}, {"color": ["blue"] * 8 + ["red"] * 2}, thresholds={"color": 0.1})
        self.assertEqual(report.metrics[0].kind, "categorical")
        self.assertEqual(report.drifted, ("color",))

    def test_feature_mismatch_and_empty_values_fail(self):
        with self.assertRaises(ValueError):
            monitor({"x": [1]}, {"y": [1]})
        with self.assertRaises(ValueError):
            monitor({"x": []}, {"x": [1]})

    def test_constant_baseline_with_shifted_current_is_drift(self):
        report = monitor({"x": [5.0, 5.0, 5.0, 5.0]}, {"x": [100.0, 100.0, 100.0, 100.0]}, thresholds={"x": 0.1})
        self.assertEqual(report.drifted, ("x",))
        self.assertEqual(monitor({"x": [5.0, 5.0]}, {"x": [5.0, 5.0]}, thresholds={"x": 0.1}).drifted, ())


if __name__ == "__main__":
    unittest.main()
