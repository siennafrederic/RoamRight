# RoamRight

Most travel planners give one-size-fits-all itineraries, but real trips need recommendations that adapt to who you are and how you travel. RoamRight is a personality-aware travel planner that generates structured multi-day itineraries with a custom retrieval + ranking + LLM generation pipeline and adapts recommendations to destination, travel style, local-vs-touristy preference, walking tolerance, and user feedback in a multi-turn refine loop.

## What It Does

RoamRight takes trip inputs from a React frontend, retrieves relevant activities from a curated attractions 
dataset, reranks those candidates with feature-based scoring, and generates day-by-day plans through a FastAPI 
backend. The system supports iterative refinement (users can provide follow-up feedback to adjust pacing/content), 
includes time-window handling for arrival/departure constraints, and outputs structured morning/afternoon/evening 
recommendations with explanation bullets.

## Current City Coverage

RoamRight currently supports trip generation for these 8 cities in the dataset: Madrid, Barcelona, Valencia, Sevilla, Paris, London, Rome, and Florence. For best results during testing/grading, please use one of these cities.

## Quick Start

For full setup details, see `docs/SETUP.md`.

1. Install Python dependencies: `pip install -r requirements.txt`
2. Start backend API: `uvicorn ui.api_server:app --reload --host 127.0.0.1 --port 8000`
3. Start frontend:
  - `cd frontend`
  - `npm install`
  - `npm run dev`
4. Open the Vite URL shown in terminal (usually `http://localhost:5173`).

## Video Links

- Product demo: [https://youtu.be/HuQ-anUlhQI](https://youtu.be/HuQ-anUlhQI)
- Technical walkthrough: [https://youtu.be/VMiNEcZsRZk](https://youtu.be/VMiNEcZsRZk)

## Evaluation

Primary evaluation artifacts:

- `docs/EVALUATION_ABLATION.md`
- `experiments/ablation_eval_summary.md`
- `experiments/ablation_eval_results.json`

To reproduce:

- `./.venv/bin/python scripts/run_ablation_eval.py`

Current ablation summary (12 benchmark requests):

- `full_pipeline`: relevance `0.4808`, diversity `0.4653`
- `no_personality`: relevance `0.3507`, diversity `0.5467`
- `no_ranking`: relevance `0.3882`, diversity `0.4621`
- `no_rag`: relevance `0.3439`, diversity `0.4193`

## Submission Notes

- Solo project submission by Sienna Frederic
- Full setup instructions: `docs/SETUP.md`
- AI tool and development attribution: `docs/ATTRIBUTION.md`
- Dataset construction methodology: `docs/DATASET_METHODOLOGY.md`
- Demo Videos: `videos/`

