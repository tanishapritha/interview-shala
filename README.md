# Interview Shala

Mobile-first interview preparation, with a role-specific roadmap and a voice-practice workflow under active development.

## Current V1 status

The repository currently contains:
- A React + Vite frontend with Clerk sign-in and an authenticated preparation-plan entry point.
- A FastAPI backend with Clerk JWT verification, candidate user records, authenticated project ownership, preparation plans, practice-session records and LiveKit token issuance.
- A separate LiveKit Agents worker using Deepgram STT, OpenRouter-compatible LLM inference, Cartesia TTS, and Silero VAD. The worker persists final transcript turns through private, shared-secret-authenticated API endpoints.
- PostgreSQL models and Alembic migrations, including normalized knowledge concepts, project knowledge maps, candidate skill profiles, ordered transcript segments, and evidence records.
- A rule-based preparation planner with optional LLM enhancement.
- Authenticated transcript segment persistence and retrieval for owned practice sessions, with sequence ordering and retry-safe writes.

**Important:** the worker implementation is now present in `apps/worker`, but it must be deployed and configured with LiveKit, Deepgram, Cartesia, OpenRouter, and the matching API worker secret before live interviews can run. The frontend does not yet provide a complete end-to-end voice room experience. Sessions are still saved without an assessment score until a trusted evaluator is connected. Browser-supplied transcript segments are unverified source material and do not count as evidence.

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

The database now separates reusable knowledge concepts from project-specific requirements and candidate-specific skill state. Skill proficiency and confidence remain nullable until trusted evidence exists. Transcript segments are ordered per session and evidence records can reference their source segment, session, project, and concept. The current transcript API accepts candidate-supplied segments and labels them `client_supplied`; it supports ordered storage and safe retries, but it is not a trusted LiveKit worker ingestion path. Client-supplied text is not used to generate scores or skill assessments. Verified worker ingestion, evidence extraction, and skill aggregation remain separate milestones.

## LiveKit worker

The worker is a separate Python service. See [apps/worker/README.md](apps/worker/README.md) and [apps/worker/.env.example](apps/worker/.env.example). Configure `WORKER_SHARED_SECRET` in both `apps/api/.env` and the worker's environment with the same long random value. Never expose it to the browser.

Local worker setup:

```powershell
cd apps/worker
python -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
# Fill LiveKit, Deepgram, Cartesia, OpenRouter and worker API settings.
python -m src.agent dev
```

The worker expects API-generated room names in the form `interview-shala-{session-uuid}`. It loads session context from the private API, starts a single interviewer agent, and persists final STT/assistant turns. A successful CI build does not verify external provider credentials, LiveKit Cloud dispatch, or real microphone/audio quality; perform an end-to-end test after deployment.

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
- Configure Clerk, LiveKit, worker shared secret, Deepgram, Cartesia, and OpenRouter credentials only in the deployment secret manager.
- Deploy `apps/worker` as a separate long-running Python service. The worker must be able to reach the API's private worker endpoints.
- A deployed API and LiveKit token endpoint do not imply that the AI interviewer worker is deployed.
