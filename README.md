# RoamRight

RoamRight is a personality-aware travel planner that generates structured multi-day itineraries using a retrieval + reranking + LLM pipeline. It adapts plans to destination, travel style, local-vs-touristy preference, walking tolerance, and user refinement feedback.

## What It Does

RoamRight takes trip inputs from a React frontend, retrieves relevant activities from a curated attractions dataset, reranks those candidates with feature-based scoring, and generates day-by-day plans through a FastAPI backend. The system supports iterative refinement (users can provide follow-up feedback to adjust pacing/content), includes time-window handling for arrival/departure constraints, and outputs structured morning/afternoon/evening recommendations with explanation bullets.

## Quick Start

For full setup details, see `SETUP.md`.

1. Install dependencies: `pip install -r requirements.txt`
2. Start backend API: `uvicorn ui.api_server:app --reload --host 127.0.0.1 --port 8000`
3. Start frontend:
   - `cd frontend`
   - `npm install`
   - `npm run dev`
4. Open the Vite URL shown in terminal (usually `http://localhost:5173`).

## Video Links

- Product demo: [https://youtu.be/HuQ-anUlhQI](https://youtu.be/HuQ-anUlhQI)
- Technical walkthrough: _TBD (will add final link in `videos/TechnicalWalkthrough.md`)_

## Evaluation

Evaluation artifacts and results:

- `EVALUATION_ABLATION.md`
- `experiments/ablation_eval_summary.md`
- `experiments/ablation_eval_results.json`

To reproduce:

- `./.venv/bin/python scripts/run_ablation_eval.py`

Current ablation summary (12 benchmark requests):

- `full_pipeline`: relevance `0.4808`, diversity `0.4653`
- `no_personality`: relevance `0.3507`, diversity `0.5467`
- `no_ranking`: relevance `0.3882`, diversity `0.4621`
- `no_rag`: relevance `0.3439`, diversity `0.4193`

## Individual Contributions

This is a single-author project submission by Sienna Frederic.

## Additional Project Notes

- Setup guide: `SETUP.md`
- Attribution: `ATTRIBUTION.md`
- Dataset methodology: `DATASET_METHODOLOGY.md`
- Video notes: `videos/`