# Semantic Cache Sim

`semantic-cache-sim` is a deterministic, dependency-free simulator for a semantic response cache. It normalizes text, compares token and bigram sets with Jaccard similarity, and combines a similarity threshold with TTL and LRU eviction. No model, network, or embedding service is required.

```powershell
python -m semantic_cache_sim --demo
python -m unittest discover -s tests -v
```

Use it as a small reference implementation when estimating cache hit rates or testing invalidation policy. The cache stores arbitrary Python values and exposes hit/miss/eviction counters for experiments.
