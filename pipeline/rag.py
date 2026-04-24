"""
Explicit RAG orchestration for RoamRight.

Stages:
1) Build query text from structured trip input.
2) Retrieve top-k activity chunks using hybrid dense+sparse retrieval.
3) Format retrieved activities into context blocks for downstream ranking/LLM steps.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.user_input import TripRequest
from retrieval.retriever import ActivityRetriever, RetrievalHit


@dataclass(frozen=True)
class RAGResult:
    """Container for RAG outputs used by later pipeline stages."""

    query_text: str
    hits: list[RetrievalHit]
    context_text: str


def format_hits_as_context(hits: list[RetrievalHit]) -> str:
    """Serialize retrieval hits into compact context for generation prompts."""
    if not hits:
        return "No relevant activities were retrieved."
    lines: list[str] = []
    for i, h in enumerate(hits, start=1):
        a = h.activity
        lines.append(
            (
                f"{i}. {a.name} [{a.category}] in {a.neighborhood}, {a.city}\n"
                f"   price_level={a.price_level} tags={', '.join(a.tags)}\n"
                f"   description={a.description}\n"
                f"   scores: hybrid={h.hybrid_score:.3f}, dense={h.dense_score:.3f}, keyword={h.keyword_score:.3f}"
            )
        )
    return "\n".join(lines)


def run_rag(
    trip: TripRequest,
    retriever: ActivityRetriever,
    top_k: int = 8,
) -> RAGResult:
    """Execute RAG retrieval stages end-to-end from one trip request."""
    query_text = trip.retrieval_query_text()
    hits = retriever.retrieve(
        query_text=query_text,
        top_k=top_k,
        city_filter=trip.destination_city,
    )
    return RAGResult(query_text=query_text, hits=hits, context_text=format_hits_as_context(hits))

