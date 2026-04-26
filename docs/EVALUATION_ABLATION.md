# Ablation Study 

## Claim Summary

RoamRight runs a controlled ablation across **three independent design choices**:

1. Retrieval grounding (RAG) on/off
2. Reranking on/off
3. Personality-aware scoring on/off

The same benchmark requests, metrics, and evaluation pipeline are used across conditions, and results are summarized in a table.

## Research Question

How much does each major pipeline component contribute to final recommendation quality?

## Experimental Design (Controlled Setup)

- Fixed benchmark set: `12` trip requests in `evaluation/benchmark_requests.py`
- Same evaluation runner for all conditions: `scripts/run_ablation_eval.py`
- Same metric definitions across all conditions:
  - relevance
  - diversity
  - latency (generation-enabled runs)
  - slot coverage (generation-enabled runs)
  - activity coverage (generation-enabled runs)
- Same aggregation logic and output format for every condition
- Results persisted to:
  - `experiments/ablation_eval_results.json` (per-trip + averages)
  - `experiments/ablation_eval_summary.md` (summary table)

## Ablation Conditions and What They Isolate

- `full_pipeline`: retrieval + reranking + personality signals (reference condition)
- `no_personality`: removes personality-aware signals while keeping retrieval/reranking
- `no_ranking`: keeps retrieval but disables post-retrieval reranking
- `no_rag`: replaces retrieval pipeline with naive city baseline

These are true methodological toggles rather than hyperparameter-only changes.

## Quantitative Results (Averages Over 12 Sample Trips)


| Approach       | Relevance | Diversity | Latency (ms) | Slot Coverage | Activity Coverage |
| -------------- | --------- | --------- | ------------ | ------------- | ----------------- |
| full_pipeline  | 0.4808    | 0.4653    | 48278.32     | 1.0000        | 0.8646            |
| no_personality | 0.3507    | 0.5467    | 45201.83     | 1.0000        | 0.8646            |
| no_ranking     | 0.3882    | 0.4621    | -            | -             | -                 |
| no_rag         | 0.3439    | 0.4193    | -            | -             | -                 |


## Delta Analysis vs Full Pipeline (Key Ablation Evidence)

Using relevance as the primary quality metric:

- `no_personality`: `0.3507` vs `0.4808` -> **-0.1301** absolute relevance
- `no_ranking`: `0.3882` vs `0.4808` -> **-0.0926** absolute relevance
- `no_rag`: `0.3439` vs `0.4808` -> **-0.1369** absolute relevance

This indicates:

- Retrieval grounding and personality are the largest contributors in this setup.
- Reranking also provides a meaningful lift beyond retrieval-only ordering.

## Interpretation

- The full system achieves the highest relevance and strong coverage.
- Removing personality improves diversity but sharply hurts relevance, consistent with a relevance-diversity tradeoff.
- Removing reranking degrades relevance while keeping diversity near the full model, showing reranking improves alignment quality.
- Removing RAG produces the weakest relevance and lower diversity, showing retrieval grounding is foundational.

## Reproducibility

Run:

`./.venv/bin/python scripts/run_ablation_eval.py`

Optional faster smoke run:

`./.venv/bin/python scripts/run_ablation_eval.py --max-trips 3 --skip-generation`

Primary evidence files:

- `scripts/run_ablation_eval.py`
- `evaluation/benchmark_requests.py`
- `evaluation/metrics.py`
- `experiments/ablation_eval_results.json`
- `experiments/ablation_eval_summary.md`

