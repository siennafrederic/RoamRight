# RoamRight React Frontend

Trendy React + Vite UI for the RoamRight planner.

## Run locally

1. Install dependencies:

```bash
npm install
```

2. Create env file:

```bash
cp .env.example .env
```

3. Start dev server:

```bash
npm run dev
```

The app expects a backend endpoint at:

- `POST /api/plan`

And uses this payload/response shape:

- Request: `src/types.ts` -> `PlanRequest`
- Response: `src/types.ts` -> `PlanResponse`

## Start backend API

From the project root:

```bash
python -m uvicorn ui.api_server:app --reload --port 8000
```

Then run the frontend in `frontend/` with `npm run dev`.
