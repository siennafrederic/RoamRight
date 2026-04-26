"""
Hybrid retriever: dense (FAISS) + keyword overlap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

import config as cfg
from data.preprocess import Activity
from retrieval.documents import activity_keyword_blob, activity_to_retrieval_doc
from retrieval.embedder import Embedder
from retrieval.faiss_index import FaissFlatIP


def _tokenize(text: str) -> set[str]:
    return {t for t in re.split(r"[^\w]+", text.lower()) if len(t) >= 2}


def keyword_overlap_score(query: str, doc_blob: str) -> float:
    """Jaccard-like overlap in [0, 1] for hybrid leg."""
    q, d = _tokenize(query), _tokenize(doc_blob)
    if not q or not d:
        return 0.0
    inter = len(q & d)
    union = len(q | d)
    return inter / union if union else 0.0


@dataclass(frozen=True)
class RetrievalHit:
    activity: Activity
    dense_score: float
    keyword_score: float
    hybrid_score: float


class ActivityRetriever:
    def __init__(self, activities: list[Activity], embedder: Embedder) -> None:
        self._activities = list(activities)
        docs = [activity_to_retrieval_doc(a) for a in self._activities]
        self._keyword_blobs = [activity_keyword_blob(a) for a in self._activities]
        mat = embedder.encode(docs)
        self._index = FaissFlatIP(mat)
        self._embedder = embedder

    def retrieve(
        self,
        query_text: str,
        top_k: int | None = None,
        city_filter: str | None = None,
    ) -> list[RetrievalHit]:
        k = top_k or cfg.DEFAULT_TOP_K
        candidates = list(range(len(self._activities)))
        if city_filter:
            cf = city_filter.strip().lower()
            candidates = [i for i in candidates if self._activities[i].city.lower() == cf]
            if not candidates:
                return []

        qv = self._embedder.encode([query_text])
        ntotal = len(self._activities)
        sims, idxs = self._index.search(qv, ntotal)
        sim_row, idx_row = sims[0], idxs[0]

        scored: list[RetrievalHit] = []
        for sim, idx in zip(sim_row.tolist(), idx_row.tolist()):
            if idx < 0 or idx not in candidates:
                continue
            act = self._activities[idx]
            kw = keyword_overlap_score(query_text, self._keyword_blobs[idx])
            dense = float(max(0.0, min(1.0, (sim + 1.0) / 2.0)))  # map IP from [-1,1] to [0,1]
            hybrid = cfg.HYBRID_DENSE_WEIGHT * dense + cfg.HYBRID_KEYWORD_WEIGHT * kw
            scored.append(
                RetrievalHit(
                    activity=act,
                    dense_score=dense,
                    keyword_score=kw,
                    hybrid_score=hybrid,
                )
            )

        scored.sort(key=lambda h: -h.hybrid_score)
        return scored[:k]
