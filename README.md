# AI Code Reviewer

AI-powered code review system with **FastAPI**, **MongoDB**, **Celery**, **Redis**, and a **React (Vite + TypeScript + shadcn/ui)** frontend.
Supports concurrent reviews, **SSE live status**, **rate limiting**, **Mongo-backed history & analytics**, and a **Redis cache** for repeated submissions.

---

## Deployed URLs

* **Frontend:** [https://ai-code-reviewer-nine-topaz.vercel.app/](https://ai-code-reviewer-nine-topaz.vercel.app/)
* **Backend (API):** [https://ai-code-reviewer-a771.onrender.com/api/](https://ai-code-reviewer-a771.onrender.com/api/)
* **API Docs (Swagger):** [https://ai-code-reviewer-a771.onrender.com/docs](https://ai-code-reviewer-a771.onrender.com/docs)

---

## Tech Stack

* **Frontend:** React + Vite + TypeScript, shadcn/ui, TanStack Query, next-themes (dark mode)
* **Backend:** FastAPI, Pydantic, Motor (MongoDB async), SSE (EventSource)
* **Worker:** Celery (Redis broker/results)
* **Database:** MongoDB
* **Infra:** Docker Compose (dev), Vercel/Netlify (FE), Render/Railway/Heroku (BE)

---

## Setup & Installation

### 1) Environment

**`backend/.env`**

```dotenv
OPENAI_API_KEY=your_openai_key
MONGODB_URI=mongodb://mongo:27017
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

# Celery / Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Rate limit
RATE_LIMIT_REDIS_URL=redis://redis:6379/1
RATE_LIMIT_PER_HOUR=10

# Cache for repeated submissions
CACHE_ENABLED=true
CACHE_REDIS_URL=redis://redis:6379/2
CACHE_TTL_SECONDS=2592000
CACHE_PREFIX=acrev:
```

**`frontend/.env`**

```dotenv
VITE_BACKEND_URL=http://localhost:8000
```

### 2) Run (Docker, recommended)

```bash
# from repo root
docker compose up -d --build
# services: api (8000), worker, mongo (27017), redis (6379)
```

### 3) Frontend (dev)

```bash
cd frontend
nvm use
npm i
npm run dev   # http://localhost:5173
```

### 4) Tests (backend)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

---

## API Documentation

OpenAPI/Swagger: `GET /docs` • Redoc: `GET /redoc`

### Health

```
GET /api/health
200 → {"status":"ok"}
```

### Submit Code for Review

```
POST /api/reviews
Body: { "language": "python" | "javascript" | "...", "code": "string" }
202 → { "id": "<submission_id>", "status": "pending" | "completed" }
```

* On **cache hit**, returns `status: "completed"` immediately (same shape).
* Rate limit: `429` if exceeded (default: 10/hour per IP).

### Get Review (Full)

```
GET /api/reviews/{id}
200 → {
  "id": "...",
  "status": "pending" | "in_progress" | "completed" | "failed",
  "created_at": "ISO",
  "updated_at": "ISO",
  "language": "python",
  "score": 1..10 | null,
  "issues": [{ "title","detail","severity","category" }] | [],
  "security": [string],
  "performance": [string],
  "suggestions": [string],
  "error": string|null
}
404 → not found
```

### Live Status (SSE)

```
GET /api/reviews/{id}/stream?interval_ms=800&ping=15000

events:
  event: status   data: pending|in_progress|completed|failed
  event: done     data: {"status":"completed|failed", "review":{...}}
```

### List Reviews (filters & pagination)

```
GET /api/reviews?language=python&status=in_progress&page=1&page_size=20&min_score=6&max_score=10
200 → { "items": [<ReviewOut>], "page":1, "page_size":20, "total": N }
```

### Analytics / Stats

```
GET /api/stats?language=python
200 → {
  "total": 123,
  "avg_score": 7.4,
  "common_issues": ["division by zero", "missing error handling", ...]
}
```

---

## Curl Quickstart

```bash
# Submit
curl -s -X POST http://localhost:8000/api/reviews \
  -H "Content-Type: application/json" \
  -d '{"language":"python","code":"def f(xs): return sum(xs)/len(xs)"}'

# Get by ID
curl -s http://localhost:8000/api/reviews/<id>

# Stream (SSE)
curl -N http://localhost:8000/api/reviews/<id>/stream
```

---

## Reset (dev)

```bash
# drop Mongo DB (dev only)
docker compose exec mongo mongosh --eval 'db.getSiblingDB("ai_code_review").dropDatabase()'

# flush Redis (ALL KEYS!) - dev only
docker compose exec redis redis-cli FLUSHALL
```

---

## Architecture Overview

* **Flow:** `POST /api/reviews` → create submission (pending) → enqueue Celery task → worker calls OpenAI with strict JSON schema → writes `reviews` → updates submission → SSE notifies clients.
* **Caching:** SHA-256 of `(language + normalized code)` → Redis → reuse existing review (returns `completed` immediately).
* **Rate limiting:** Redis counter per-IP/hour.
* **DB Indexes:** `submissions` (`status`, `(language,created_at)`, `(ip,created_at)`, `review_id`, `code_hash`), `reviews` (`submission_id` unique, `created_at`, `(score,created_at)`, `issues.title`).

---

## Design Notes

We chose FastAPI + Motor for a fully async API that scales under concurrent I/O with Mongo, Redis, and OpenAI. Celery isolates slow/variable LLM calls, keeping API latency low and enabling horizontal scaling. Redis plays three roles: Celery broker/results, precise rate limiting, and a cache that deduplicates repeated submissions by `(language + code)` SHA-256, reducing cost and turnaround.

Reviews follow a schema-driven prompt with a rubric, producing consistent scores and structured issues (`title`, `detail`, `severity`, `category`). We request JSON-only outputs and normalize values before persisting. Data is stored in Mongo to power history and analytics; we denormalize minimal fields (e.g., `language`) for efficient filtering. Aggregations compute averages and common issues using `$unwind`/`$group`/`$sort`, backed by indexes.

SSE provides simple live status without polling. We ship anti-buffering headers and periodic `ping` to keep connections healthy through proxies; the client treats “incomplete chunk” closes after `done` as normal. The frontend uses Vite + TS with shadcn/ui for accessible components (Progress, Cards) and next-themes for dark mode. A small status→progress map clarifies task state, and a live list surfaces active submissions; clicking opens details and hides the editor.

Scalability: API and worker scale independently; Redis/Mongo can be managed services. With higher volume, we would add idempotent enqueue locks, bulk updates, structured logging, alerts, and per-user auth/quotas. We’d also ship richer diffs, more granular analytics per language and pre-warmed cache for common snippets.

Challenges included strict CORS (credentials vs wildcard), SSE lifecycle quirks in browsers, event‑loop management in tests/workers, and async Mongo initialization. In tests we hit “Event loop is closed” from Motor during teardown; we fixed this by running the app under a lifespan manager, using httpx AsyncClient with ASGI transport, avoiding truthiness checks on Motor Database (use db is not None), passing a per-test DB into init_db(_db), and dropping it before the loop closes. In the Celery worker we saw loop errors after forking; we isolated each task with asyncio.run(...), initialized Mongo inside the worker process (instead of reusing API globals), and switched to redis.asyncio to avoid aioredis import conflicts. For dev startup we moved DB init and index creation into FastAPI’s lifespan, which removed race conditions at boot. We also normalized Pydantic payloads and categories to satisfy strict validators. Trade-offs prioritized core functionality and clear extension points; tests cover rate limiting, stats, SSE, cache hits, and end‑to‑end flow.
