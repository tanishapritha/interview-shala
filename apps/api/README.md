# Interview Shala API

FastAPI backend for the mobile-first Voice AI interview preparation product.

## Requirements

- Python 3.12+
- PostgreSQL 14+ (async via `asyncpg`)

## Setup

```bash
cd apps/api
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit DATABASE_URL, Clerk, LiveKit, optional LLM keys
```

## Database

```bash
alembic upgrade head
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

- Health: `GET http://localhost:8000/api/v1/health`
- Docs: `http://localhost:8000/docs`

From the monorepo root you can also run `pnpm dev:api`.

## Auth

| Mode | How |
|------|-----|
| Anonymous | `POST /api/v1/auth/anonymous` → send `X-Anonymous-Session` |
| Authenticated | Clerk Bearer JWT |
| Migrate | `POST /api/v1/auth/migrate` with Clerk JWT + anonymous session |

## Quick start

```bash
curl -X POST http://localhost:8000/api/v1/projects/quick-start \
  -H "Content-Type: application/json" \
  -H "X-Anonymous-Session: <session_id>" \
  -d '{"company":"Acme","role":"Backend Engineer"}'
```

Works without LLM keys (template planner). Set `GROQ_API_KEY` or `OPENROUTER_API_KEY` to enhance plans.

## Tests

```bash
pytest
```

Unit tests cover health + planner and do not require a database.

## Docker

```bash
docker build -t interview-shala-api .
docker run --env-file .env -p 8000:8000 interview-shala-api
```
