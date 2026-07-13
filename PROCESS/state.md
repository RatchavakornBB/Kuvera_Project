## Current
Phase: 3 (Contracts, Concierge, Chat)
Active task: phase3-001-contracts-lead
Status: in_progress
Last checkpoint commit: a0fddba
Blocked on: nothing

## Next up
phase3-002-concierge-qa, phase3-003-chat-panel, phase3-004-chat-websocket,
phase3-005-web-search-edgar — per docs/5day-build-timeline.md Section 6 Phase 3.
User asked to run through all of Phase 3 continuously (2026-07-13).

## Open questions for user
- none currently open

## Environment notes (read before assuming state)
- Local Supabase for this project runs on shifted ports 55321 (API), 55322 (DB), 55323 (Studio), 55324 (Inbucket/SMTP), 55327 (Analytics) — NOT the 54321 default (D-004).
- Docker Desktop is not always running by default on this machine — check `docker ps` before assuming Supabase is up. After any `supabase db reset`, wait for all containers `(healthy)` before hitting Storage.
- `.env` has real ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY, DATABASE_URL. Never print/log/commit these.
- Every new `public` table/migration needs its own `GRANT ... TO service_role` block (D-005).
- `supabase/seed.sql`: demo user (demo@kuvera.capital / kuvera-demo) + 3 deals (Deal A, Horizon Freight Corp, Nova Fintech).
- Backend: `/health`, `/deals` (GET/POST/{id}), `/deals/{id}/documents` (upload), `/deals/{id}/analyze` (full Analyst Lead graph, ~45s). `sys.path` self-bootstraps in main.py (D-009) for the agents/ cross-package import.
- Agents (`agents/`): standalone, own config/db (D-007). Every node MUST wrap its full body (fetches + model call + parsing) in `with_retry`, not just the model call (D-008, D-010). doc_summarizer/risk_flagger/ic_memo_drafter/pricing_advisor + graph.py (gate + Send() fan-out, Postgres Checkpointer) all done and verified in Phase 2.
- Frontend Dashboard (Board/Kanban) wired to real `/deals`. Table/Pipeline/Chat/Deal Detail/Documents/Agent Hub/Admin screens still unbuilt.
