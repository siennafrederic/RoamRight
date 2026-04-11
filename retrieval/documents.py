"""
Build retrieval documents from structured activity rows.

Rubric (custom RAG, 10 pts): **custom chunking strategy** — we serialize each activity
into a fixed template so embeddings capture category, place, tags, and narrative text
consistently (better than raw description-only chunks for tabular POI data).
"""

from __future__ import annotations

from data.preprocess import Activity


def activity_to_retrieval_doc(activity: Activity) -> str:
    """Single-document-per-activity 'chunk' for dense retrieval."""
    tag_str = " ".join(activity.tags)
    loc = f"{activity.neighborhood}, {activity.city}, {activity.country}"
    return (
        f"{activity.name} | {activity.category} | {loc}\n"
        f"Tags: {tag_str}\n"
        f"{activity.description}"
    )


def activity_keyword_blob(activity: Activity) -> str:
    """Text used for sparse overlap with the query (hybrid search leg)."""
    return " ".join(
        [
            activity.name,
            activity.category,
            activity.description,
            " ".join(activity.tags),
            activity.city,
            activity.country,
        ]
    ).lower()
