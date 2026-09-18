# Model Drift Monitor

An offline, stdlib-only monitor for detecting changes between a baseline feature distribution and a current window. Numeric features use a fixed-width histogram and population stability index (PSI); categorical features use Jensen-Shannon divergence. Results are deterministic and JSON serializable.

```powershell
python -m model_drift_monitor --demo
python -m unittest discover -s tests -v
```

This is intentionally a small monitoring primitive: it does not load a model, call a service, or infer labels. Feed it already-collected feature values and choose thresholds appropriate to the application.
