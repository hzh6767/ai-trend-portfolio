import unittest

from semantic_cache_sim import SemanticCache, similarity


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class SemanticCacheTests(unittest.TestCase):
    def test_similarity_and_semantic_hit(self):
        self.assertEqual(similarity("", ""), 1.0)
        cache = SemanticCache[str](similarity_threshold=0.5)
        cache.put("How do I reset my password?", "reset-help")
        self.assertEqual(cache.get("How can I reset my password?"), "reset-help")
        self.assertEqual(cache.stats().hits, 1)

    def test_lru_eviction(self):
        cache = SemanticCache[str](max_entries=2, similarity_threshold=1.0)
        cache.put("one", "1")
        cache.put("two", "2")
        self.assertEqual(cache.get("one"), "1")
        cache.put("three", "3")
        self.assertIsNone(cache.get("two"))
        self.assertEqual(cache.stats().evictions, 1)

    def test_ttl_expiry_counts_as_miss(self):
        clock = Clock()
        cache = SemanticCache[str](ttl_seconds=5, clock=clock, similarity_threshold=1.0)
        cache.put("hello", "world")
        clock.now = 5
        self.assertIsNone(cache.get("hello"))
        self.assertEqual(cache.stats().misses, 1)


if __name__ == "__main__":
    unittest.main()
