"""Small semantic cache with deterministic similarity and LRU behavior."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import re
import time
from typing import Callable, Generic, TypeVar

T = TypeVar("T")
_WORD_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?", re.IGNORECASE)


def _features(text: str) -> frozenset[str]:
    words = [part.lower() for part in _WORD_RE.findall(text)]
    features = set(words)
    features.update(f"{left} {right}" for left, right in zip(words, words[1:]))
    return frozenset(features)


def similarity(left: str, right: str) -> float:
    """Return token/bigram Jaccard similarity in the inclusive range [0, 1]."""
    if not isinstance(left, str) or not isinstance(right, str):
        raise TypeError("similarity inputs must be strings")
    left_features, right_features = _features(left), _features(right)
    if not left_features and not right_features:
        return 1.0
    if not left_features or not right_features:
        return 0.0
    return len(left_features & right_features) / len(left_features | right_features)


@dataclass(frozen=True)
class CacheStats:
    hits: int
    misses: int
    evictions: int
    size: int

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    def as_dict(self) -> dict[str, float | int]:
        return {"hits": self.hits, "misses": self.misses, "evictions": self.evictions, "size": self.size, "hit_rate": round(self.hit_rate, 6)}


@dataclass
class _Entry(Generic[T]):
    query: str
    value: T
    created_at: float
    last_access: float


class SemanticCache(Generic[T]):
    """An in-memory semantic cache suitable for repeatable experiments."""

    def __init__(
        self,
        max_entries: int = 128,
        similarity_threshold: float = 0.86,
        ttl_seconds: float | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be positive")
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError("similarity_threshold must be in [0, 1]")
        if ttl_seconds is not None and ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self.max_entries = max_entries
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self._clock = clock
        self._entries: OrderedDict[str, _Entry[T]] = OrderedDict()
        self._hits = self._misses = self._evictions = 0

    def put(self, query: str, value: T) -> None:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        now = self._clock()
        key = query.strip().lower()
        self._entries.pop(key, None)
        self._entries[key] = _Entry(query, value, now, now)
        while len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)
            self._evictions += 1

    def get(self, query: str, default: T | None = None) -> T | None:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        now = self._clock()
        self._expire(now)
        best_key: str | None = None
        best_score = -1.0
        for key, entry in self._entries.items():
            score = similarity(query, entry.query)
            if score >= self.similarity_threshold and score > best_score:
                best_key, best_score = key, score
        if best_key is None:
            self._misses += 1
            return default
        entry = self._entries.pop(best_key)
        entry.last_access = now
        self._entries[best_key] = entry
        self._hits += 1
        return entry.value

    def invalidate(self, query: str) -> bool:
        return self._entries.pop(query.strip().lower(), None) is not None

    def clear(self) -> None:
        self._entries.clear()

    def stats(self) -> CacheStats:
        self._expire(self._clock())
        return CacheStats(self._hits, self._misses, self._evictions, len(self._entries))

    def _expire(self, now: float) -> None:
        if self.ttl_seconds is None:
            return
        expired = [key for key, entry in self._entries.items() if now - entry.created_at >= self.ttl_seconds]
        for key in expired:
            del self._entries[key]
            self._evictions += 1
