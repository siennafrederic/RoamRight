# RoamRight

RoamRight is a personalized travel-planning system that combines retrieval, reranking, and LLM generation to produce multi-day itineraries based on user preferences (destination, interests, walking tolerance, tourist-vs-local balance, and travel style). The pipeline loads and preprocesses a curated activity dataset, retrieves relevant candidates with hybrid semantic + keyword search, reranks candidates with feature-based scoring, and generates a structured day-by-day plan through a FastAPI backend consumed by a React frontend, with support for iterative refinement from user feedback.

## What It Does

RoamRight takes a trip request and generates a customized itinerary with morning/afternoon/evening suggestions for each day, top activity picks, and explanation bullets describing planning tradeoffs. It supports personalization controls (interests, travel pace, group type, local-vs-touristy preference, and mobility constraints), then uses a multi-stage ML pipeline (retrieval -> ranking -> generation) to produce coherent plans. Users can refine an existing itinerary by providing natural-language feedback, and the backend regenerates an updated plan while preserving trip context.

## Quick Start

For full setup details, see `SETUP.md`.

1. Install Python dependencies from `requirements.txt`.
2. Start backend API:
   - `uvicorn ui.api_server:app --reload --port 8000`
3. In `frontend/`, install JS dependencies and run the dev server:
   - `npm install`
   - `npm run dev`
4. Open the Vite URL shown in terminal (typically `http://localhost:5173`).

## Project Structure

- `ui/` - FastAPI server and API endpoints
- `pipeline/` - orchestration logic for retrieval, ranking, and generation
- `retrieval/` - embedding and hybrid retrieval components
- `ranking/` - feature-based reranking logic
- `evaluation/` - benchmark requests and metric definitions
- `scripts/` - runnable evaluation and smoke-test scripts
- `frontend/` - React + Vite user interface

## Evaluation

Quantitative results and analysis are documented in:

- `EVALUATION_ABLATION.md` (controlled ablation study and interpretation)
- `experiments/ablation_eval_summary.md` (summary table artifact)
- `experiments/ablation_eval_results.json` (per-trip and aggregate outputs)

To reproduce evaluation:

- `./.venv/bin/python scripts/run_ablation_eval.py`

## Video Links

- Demo video: _TBD_
- Technical walkthrough video: _TBD_

## Render Deployment (Public URL)

This repository includes `render.yaml` for one-click Render blueprint deployment:

- `roamright-api` (FastAPI backend)
- `roamright-frontend` (Vite static frontend)

After creating both services on Render:

1. Copy your backend URL (for example `https://roamright-api.onrender.com`).
2. In the frontend Render service, set:
   - `VITE_API_BASE_URL=<your-backend-url>`
3. In the backend Render service, set:
   - `CORS_ALLOW_ORIGINS=<your-frontend-url>`
   - `LLM_API_KEY=<your-key>`
4. Redeploy both services.
