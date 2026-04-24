"""
Pre-LLM orchestration pipeline: parse input -> retrieve -> rank.
"""

from __future__ import annotations

from dataclasses import dataclass

import config as cfg
from data.preprocess import Activity, load_and_preprocess
from models.user_input import TripRequest
from pipeline.rag import RAGResult, run_rag
from ranking.scorer import RankedHit, rank_hits
from retrieval.embedder import Embedder
from retrieval.retriever import ActivityRetriever


@dataclass(frozen=True)
class PipelineOutput:
    trip: TripRequest
    rag: RAGResult
    ranked_hits: list[RankedHit]


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
        return PipelineOutput(trip=trip, rag=rag, ranked_hits=ranked)
