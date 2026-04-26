# SETUP

This guide provides step-by-step instructions to run RoamRight locally.

## Prerequisites

- Python 3.10+ (3.11 recommended)
- Node.js 18+ and npm
- Git

## 1) Clone and enter the project

```bash
git clone <your-repo-url>
cd RoamRight
```

## 2) Create and activate a Python virtual environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## 3) Install backend dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 4) Configure environment variables

RoamRight reads backend settings from a root `.env` file.

Create `.env` in the repository root and set values such as:

- `LLM_PROVIDER` (`ollama` or `openai_compatible`)
- `LLM_MODEL`
- `LLM_BASE_URL`
- `LLM_API_KEY` (if required by provider)
- `ROAMRIGHT_ACTIVITIES_PATH` (optional override for dataset file)

Notes:

- Default behavior targets a local Ollama-compatible endpoint.
- If using hosted providers, ensure API key and base URL are set correctly.

## 5) Start the backend API server

From repo root:

```bash
uvicorn ui.api_server:app --reload --host 127.0.0.1 --port 8000
```

Health check:

- Open `http://127.0.0.1:8000/api/health`
- Expected response: `{"status":"ok"}`

## 6) Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Then open the printed Vite URL (typically `http://localhost:5173`).

## 7) Optional: run evaluation

From repo root (with virtual environment active):

```bash
./.venv/bin/python scripts/run_ablation_eval.py
```

Outputs:

- `experiments/ablation_eval_results.json`
- `experiments/ablation_eval_summary.md`

## 8) Optional: LLM connectivity smoke test

```bash
./.venv/bin/python scripts/smoke_test_llm.py
```

## 9) Deploy on Render (for public demo URL)

This repo includes a Render blueprint at `render.yaml` that defines:

- `roamright-api` (Python web service)
- `roamright-frontend` (static site)

### Deploy steps

1. Push this repository to GitHub.
2. In Render, choose **New + -> Blueprint** and connect your repo.
3. Render will detect `render.yaml` and create both services.
4. Once the backend service URL is available, copy it.
5. In Render dashboard:
   - Frontend service env var:
     - `VITE_API_BASE_URL=https://<your-backend>.onrender.com`
   - Backend service env vars:
     - `CORS_ALLOW_ORIGINS=https://<your-frontend>.onrender.com`
     - `LLM_API_KEY=<your_api_key>`
6. Redeploy both services and test:
   - `https://<your-backend>.onrender.com/api/health`
   - `https://<your-frontend>.onrender.com`

Notes:

- Free-tier cold starts can add response latency.
- Keep secrets only in Render environment variables, not in git-tracked files.

## Common Troubleshooting

- **Import errors**: ensure virtual environment is activated and `pip install -r requirements.txt` completed.
- **Frontend cannot reach backend**: ensure backend is running on port `8000` and frontend on `5173`.
- **LLM call failures**: verify `.env` provider settings and API key/base URL.
- **Slow first run**: sentence-transformer model download can take time on first use.
