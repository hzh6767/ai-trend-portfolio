# rag-eval-kit

Small, deterministic RAG evaluation toolkit for local experiments and CI.
It measures context precision/recall, citation precision/recall, and answer
grounding without an LLM, network access, or API keys. The implementation uses
token overlap and sentence-level support so the result is reproducible.

## Quick start

```text
python -m unittest discover -s tests -v
python -m pip install -e .
python -m rag_eval_kit --demo
```

The package is intentionally stdlib-only. From the project directory, the
module is importable after the editable install:

```text
python -m pip install -e .
python -m rag_eval_kit --demo --json
```

Evaluate a custom case with repeated context arguments:

```text
python -m rag_eval_kit --query "refund window" \
  --answer "Customers can request a refund within 30 days." \
  --context policy::Refunds are available within 30 days of purchase. \
  --citation policy
```

## Metrics

* **Context precision**: relevant retrieved documents divided by retrieved
  documents. If no gold IDs are supplied, a document is relevant when it has
  non-empty token overlap with the query.
* **Context recall**: gold relevant document IDs found in the retrieved set.
* **Citation precision**: cited documents that exist and support at least one
  answer claim divided by unique cited documents.
* **Citation recall**: gold citation IDs found in the cited set.
* **Grounding**: mean best token-F1 between each non-empty answer sentence and
  an evidence document.

All scores are in the inclusive range `[0, 1]`. Empty inputs are handled
explicitly rather than producing NaN values. This is a lightweight signal for
regression testing, not a replacement for human review or model-based judging.

## Layout

```text
src/rag_eval_kit/  library and CLI
tests/             stdlib unittest coverage
```
