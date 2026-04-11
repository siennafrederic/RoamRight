"""In-memory FAISS index for dense retrieval."""

from __future__ import annotations

import faiss
import numpy as np


class FaissFlatIP:
    """Inner product on L2-normalized vectors ≈ cosine similarity."""

    def __init__(self, vectors: np.ndarray) -> None:
        if vectors.ndim != 2:
            raise ValueError("vectors must be 2D")
        dim = vectors.shape[1]
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(vectors.astype(np.float32, copy=False))

    def search(self, query_vectors: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
        return self._index.search(query_vectors.astype(np.float32, copy=False), k)
