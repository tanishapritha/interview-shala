# Implementation status

Audit snapshot: 2026-11-02. This file describes repository code, not a live deployment.

## Working foundations

- FastAPI application, API router and health endpoint.
- PostgreSQL SQLAlchemy models and initial Alembic migration.
- Anonymous signed-session issuance and verification.
- Clerk JWT verification and anonymous-project migration endpoint.
- Project CRUD, quick-start planner, preparation plan/task endpoints.
- Practice-session creation, retrieval and LiveKit token issuance.
- Role-bucket template planner with optional LLM enhancement.
- Weakness/evidence persistence for trusted low scores.
- React/Vite/TypeScript workspace, design tokens, responsive primitives and Zustand store.
- Mobile-first quick-start and preparation-plan screen added in this branch.
- Backend evaluation now refuses client-provided scores and does not invent a numeric score before transcript evaluation exists.
- Backend regression tests and GitHub Actions CI added in this branch.

## Partially implemented

- Anonymous session continuity currently relies on a signed bearer token stored by the frontend persistence store. It is not an HttpOnly cookie.
- Clerk verification and account migration exist, but the frontend Clerk sign-in and migration journey is not wired into the new entry screen.
- LiveKit credentials can be issued, but the repository does not yet contain a functioning LiveKit Agents worker.
- Session records can be completed, but transcript persistence and evidence-based scoring are not connected end to end.
- Weakness tracking persists low-score evidence, but lifecycle states (active/improving/resolved), deduplication policy and longitudinal trend semantics need a dedicated migration and tests.
- Preparation tasks can be displayed and updated through the API; task checkbox persistence in the new UI is not wired.
- PWA manifest is configured; production installability and offline behavior need browser/device verification.

## Missing or not verified

- A real-time AI interviewer worker with STT/LLM/TTS provider adapters, interruption handling, reconnects and transcript persistence.
- Trusted transcript evaluation with rubric versioning, evidence excerpts, confidence and evaluator provenance.
- HttpOnly anonymous-session cookie flow and account-migration UX.
- Complete practice room, session report, analytics and weakness screens.
- Browser-driven mobile viewport and accessibility testing.
- Deployment configuration and live smoke tests for frontend, API, database and worker.
- Production rate limits, SSRF protections for external URL ingestion, upload validation and provider-secret lifecycle review.
- Verified CI result for the branch. CI is configured but must run on GitHub after the PR is opened.

## Release gates

1. Run the CI workflow successfully.
2. Test anonymous quick-start against a real PostgreSQL database.
3. Verify project ownership isolation for anonymous and Clerk identities.
4. Confirm no client input can set scores, strengths or improvement feedback.
5. Implement and deploy the LiveKit agent worker before advertising voice practice.
6. Persist transcripts and evaluate them server-side before displaying readiness scores.
7. Move anonymous bearer credentials to secure HttpOnly cookies before production.
8. Run Playwright at 320, 360, 375, 390, 414, 430, 768, 1024 and 1440 CSS pixels.
9. Verify hosted migrations, CORS, secrets, rate limits and health checks.
