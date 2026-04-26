"""
Pre-LLM orchestration pipeline: parse input -> retrieve -> rank.
"""

from __future__ import annotations

from dataclasses import dataclass

import config as cfg
from data.preprocess import Activity, load_and_preprocess
from models.user_input import TripRequest
from pipeline.rag import RAGResult, run_rag
from pipeline.resolve import ResolvedMustInclude, resolve_must_includes
from pipeline.schedule import ScheduledItem, build_timed_schedule
from ranking.scorer import RankedHit, rank_hits
from retrieval.embedder import Embedder
from retrieval.retriever import ActivityRetriever


@dataclass(frozen=True)
class PipelineOutput:
    trip: TripRequest
    rag: RAGResult
    ranked_hits: list[RankedHit]
    resolved_must_includes: list[ResolvedMustInclude]
    scheduled_items: list[ScheduledItem]


class RoamRightPipeline:
    """
    Reusable pipeline object so index construction happens once.
    """

    def __init__(self, activities: list[Activity] | None = None) -> None:
        self.activities = activities or load_and_preprocess(cfg.ACTIVITIES_PATH)
        self.embedder = Embedder(cfg.EMBEDDING_MODEL_NAME)
        self.retriever = ActivityRetriever(self.activities, self.embedder)

    def run(self, trip: TripRequest, top_k_retrieval: int = 16, top_k_ranked: int = 8) -> PipelineOutput:
        rag = run_rag(trip=trip, retriever=self.retriever, top_k=top_k_retrieval)
        ranked = rank_hits(rag.hits, trip=trip, top_k=top_k_ranked)
        resolved = resolve_must_includes(trip=trip, activities=self.activities)
        schedule = build_timed_schedule(trip=trip, ranked_hits=ranked)
        return PipelineOutput(
            trip=trip,
            rag=rag,
            ranked_hits=ranked,
            resolved_must_includes=resolved,
            scheduled_items=schedule,
        )
