# Interview Shala

Mobile-first interview preparation, with a role-specific roadmap and a voice-practice workflow under active development.

## Current V1 status

The repository currently contains:
- A React + Vite frontend with an anonymous quick-start and preparation-plan view.
- A FastAPI backend with anonymous sessions, project ownership, preparation plans, practice-session records and LiveKit token issuance.
- PostgreSQL models and Alembic migrations.
- A rule-based preparation planner with optional LLM enhancement.

**Important:** a LiveKit token endpoint is not the same as a running AI interviewer. The real-time agent worker and evidence-backed transcript evaluation are not yet complete. Sessions are currently saved without an assessment score until a trusted evaluator is connected. Do not treat a saved session as an evaluated interview.

## Requirements

- Node.js 20+
- pnpm 10+
- Python 3.12+
- PostgreSQL 14+

## Local development

### 1. Backend

```bash
cd apps/api
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Set DATABASE_URL and ANONYMOUS_SESSION_SECRET
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Health: http://localhost:8000/api/v1/health  
API docs: http://localhost:8000/docs

### 2. Frontend (second terminal)

```bash
pnpm install
pnpm dev:web
```

Open http://localhost:5173. Vite proxies `/api` to the local API. Alternatively set `VITE_API_URL` to the API origin.

### 3. Root scripts

- `pnpm dev:web` — frontend.
- `pnpm dev:api` — backend (requires the API virtual environment and dependencies).
- `pnpm build` — frontend production build.
- `pnpm lint` — frontend lint.
- `pnpm typecheck` — frontend TypeScript check.

Run the frontend and backend in separate terminals.

## Environment

See [root .env.example](.env.example) and [API .env.example](apps/api/.env.example). Never commit real credentials. The anonymous session token is currently persisted by the frontend store; use only a strong production secret and treat browser storage as bearer credentials. Moving this to secure HttpOnly cookies remains a production-hardening task.

## Database

```bash
cd apps/api
alembic upgrade head
```

Use a direct PostgreSQL connection for migrations if your hosted provider separates pooled runtime and direct migration URLs.

## Tests

```bash
cd apps/api
pip install -e ".[dev]"
pytest
ruff check app tests
```

From the root:

```bash
pnpm install
pnpm typecheck
pnpm lint
pnpm build
```

## Authentication

- Anonymous: `POST /api/v1/auth/anonymous`, then send the returned `sessionId` in the `X-Anonymous-Session` header.
- Authenticated: Clerk Bearer JWT.
- Migration: `POST /api/v1/auth/migrate` with a Clerk JWT and the anonymous session ID.

## Deployment notes

- Deploy `apps/api` as a Python 3.12 service using its Dockerfile.
- Deploy `apps/web` as a Vite static site.
- Configure the frontend API origin and backend CORS allowlist.
- Run Alembic migrations before routing traffic.
- Configure Clerk and LiveKit credentials only in the deployment secret manager.
- A deployed API and LiveKit token endpoint do not imply that the AI interviewer worker is deployed.
