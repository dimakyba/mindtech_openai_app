# MindTech OpenAI Integration App

A minimal full‑stack demo that processes text via an OpenAI‑powered backend with four modes:

- summarize
- rephrase (tone: casual, professional, friendly)
- extract_json (returns structured JSON)
- classify sentiment

Frontend is a React + Vite app (Tailwind UI). Backend is FastAPI.

## Prerequisites

- Python 3.10+
- Node.js 18+

## 1) Configure environment

Create a `.env` in the repo root (see `env.example`):

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
SUMMARIZE_PROMPT_ID=pmpt_...
REPHRASE_PROMPT_ID=pmpt_...
EXTRACT_JSON_PROMPT_ID=pmpt_...
CLASSIFY_SENTIMENT_PROMPT_ID=pmpt_...

# Optional rate limiting (defaults shown)
RATE_LIMIT_REQUESTS=20
RATE_LIMIT_WINDOW_SEC=60
```

## 2) Run the backend

```bash
cd backend
pip install -r ../requirements.txt
uvicorn app:app --reload --port 8000
```

API base: `http://localhost:8000`

## 3) Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open: `http://localhost:5173`

The frontend calls the backend at `/api/run` (same origin in production; in dev, ensure your browser can reach `http://localhost:8000`). If needed, configure a Vite proxy in `frontend/vite.config.js`.

## API

- __POST__ `/api/run`

Request:

```json
{
  "mode": "summarize" | "rephrase" | "extract_json" | "classify",
  "text": "1..5000 chars",
  "tone": "casual" | "professional" | "friendly"
}
```

Notes:
- `tone` is required only when `mode` = `rephrase`.

Response:

```json
{
  "result": "string or JSON",
  "usage": { "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0 }
}
```

## Frontend features

- Character counter with validation (1–5000)
- Mode + conditional Tone select
- Copy result
- JSON pretty‑print with syntax highlighting
- Usage panel (prompt / completion / total tokens)

## Tests

Run backend tests from repo root:

```bash
pytest -q
```

Included checks (see `tests/test_api.py`):
- summarize returns 200 + non‑empty
- rephrase missing tone → 400
- classify returns allowed label
- extract_json returns valid JSON
- rate‑limit returns 429 after threshold

## Deployment notes

- Provide all env vars at deploy time (never hardcode keys in the frontend).
- Serve the built frontend (Vite `npm run build`) behind the FastAPI app or a static host; point the UI to the API origin.

## Screenshots

![UI](screenshot_ui.png)

![JSON](screenshot_json.png)