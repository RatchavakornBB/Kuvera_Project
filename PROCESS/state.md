## Current
Phase: 2 (Core AI Loop) — Phase 1 Foundations complete
Active task: phase2-001-documents-upload (about to start)
Status: starting
Last checkpoint commit: 5f8c124
Blocked on: nothing

## Next up
phase2-002-model-adapter, then 3.1 doc_summarizer, 3.2 risk_flagger + gate/fan-out,
3.3 ic_memo_drafter (+ 3.4 pricing_advisor if time allows), then /deals/{id}/analyze
end to end — per docs/5day-build-timeline.md Section 6 Phase 2. User asked to run
through all of Phase 2 continuously (2026-07-12).

## Open questions for user
- none currently open

## Environment notes (read before assuming state)
- Local Supabase for this project runs on shifted ports 55321 (API), 55322 (DB), 55323 (Studio), 55324 (Inbucket/SMTP), 55327 (Analytics) — NOT the 54321 default (D-004).
- Docker Desktop is not always running by default on this machine — check `docker ps` before assuming Supabase is up (AGENT.md Section 4).
- `.env`'s `ANTHROPIC_API_KEY` is a real key. Never print, log, or commit its value.
- Core schema (8 tables) live via `supabase/migrations/20260712162858_create_core_schema.sql`. New public tables need a `GRANT ... TO service_role` block (D-005).
- `supabase/seed.sql`: demo user (demo@kuvera.capital / kuvera-demo, Partner, can sign in) + 3 deals (Deal A, Horizon Freight Corp, Nova Fintech). Seeded auth.users rows need every `*_token`/`email_change*` column set to `''` (D-006).
- Backend has `/health`, `/deals` (GET/POST), `/deals/{id}` (GET) — service layer in `app/services/deals.py`, Supabase client singleton in `app/db.py`. CORS open to `http://localhost:5173` only.
- Frontend Dashboard (Board/Kanban) wired to real `/deals` data via TanStack Query (`src/lib/api.ts`). Table/Pipeline view not built yet (phase1-007, backlogged).
