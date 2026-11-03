# Interview Shala

Mobile-first interview preparation, with a role-specific roadmap and a voice-practice workflow under active development.

## Current V1 status

The repository currently contains:
- A React + Vite frontend with Clerk sign-in and an authenticated preparation-plan entry point.
- A FastAPI backend with Clerk JWT verification, candidate user records, authenticated project ownership, preparation plans, practice-session records and LiveKit token issuance.
- PostgreSQL models and Alembic migrations, including normalized knowledge concepts, project knowledge maps, candidate skill profiles, ordered transcript segments, and evidence records.
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
# Set DATABASE_URL, CLERK_SECRET_KEY and CLERK_JWKS_URL
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

Open http://localhost:5173. Vite loads frontend environment variables from the repository root and proxies `/api` to the local API. Set `VITE_CLERK_PUBLISHABLE_KEY` in the root `.env`. Alternatively set `VITE_API_URL` to the API origin.

### 3. Root scripts

- `pnpm dev:web` — frontend.
- `pnpm dev:api` — backend (requires the API virtual environment and dependencies).
- `pnpm build` — frontend production build.
- `pnpm lint` — frontend lint.
- `pnpm typecheck` — frontend TypeScript check.

Run the frontend and backend in separate terminals.

## Environment

See [root .env.example](.env.example) and [API .env.example](apps/api/.env.example). Never commit real credentials. The anonymous session token is currently persisted by the frontend store; use only a strong production secret and treat browser storage as bearer credentials. Moving this to secure HttpOnly cookies remains a production-hardening task.

## Candidate intelligence data foundation

The database now separates reusable knowledge concepts from project-specific requirements and candidate-specific skill state. Skill proficiency and confidence remain nullable until trusted evidence exists. Transcript segments are ordered per session and evidence records can reference their source segment, session, project, and concept. These are persistence primitives; ingestion, evidence extraction, and skill aggregation are separate implementation milestones and are not implied to be active yet.

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

- Frontend: set `VITE_CLERK_PUBLISHABLE_KEY` in the repository-root `.env`.
- Backend: set `CLERK_SECRET_KEY` and `CLERK_JWKS_URL` in `apps/api/.env`.
- Authenticated API requests use a Clerk session JWT in the `Authorization: Bearer` header.
- `GET /api/v1/auth/me` provisions or returns the internal candidate profile for the verified Clerk user.
- Candidate data endpoints require Clerk authentication. The legacy anonymous session and migration endpoints remain only to support migration of existing anonymous preparation data.

## Deployment notes

- Deploy `apps/api` as a Python 3.12 service using its Dockerfile.
- Deploy `apps/web` as a Vite static site.
- Configure the frontend API origin and backend CORS allowlist.
- Run Alembic migrations before routing traffic.
- Configure Clerk and LiveKit credentials only in the deployment secret manager.
- A deployed API and LiveKit token endpoint do not imply that the AI interviewer worker is deployed.
