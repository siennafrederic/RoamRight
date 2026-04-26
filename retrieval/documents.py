"""
Build retrieval documents from structured activity rows.
"""

from __future__ import annotations

from data.preprocess import Activity


def activity_to_retrieval_doc(activity: Activity) -> str:
    """Single-document-per-activity 'chunk' for dense retrieval."""
    tag_str = " ".join(activity.tags)
    loc = f"{activity.neighborhood}, {activity.city}, {activity.country}"
    duration_str = f"{activity.duration_minutes} minutes" if activity.duration_minutes else "duration unknown"
    return (
        f"{activity.name} | {activity.category} | {loc}\n"
        f"Tags: {tag_str}\nDuration: {duration_str}\n"
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
