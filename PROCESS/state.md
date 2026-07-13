## Current
Phase: 4 (Integration)
Active task: full-integration-pass (Dashboard -> Deal Detail -> Chat, uninterrupted)
Status: in_progress
Last checkpoint commit: 8dab695
Blocked on: nothing

## Next up
Full integration pass: click through Dashboard -> Deal Detail (all 4 tabs) -> Documents
& Contracts -> Agent Hub -> Chat as one uninterrupted flow, fix any broken links/state.
This is the last item before Phase 4 is complete (5day-build-timeline.md's final Phase 4
block, 16:00-17:30). User asked to do all of this continuously (2026-07-13).

## Open questions for user
- none currently open

## Environment notes (read before assuming state)
- Local Supabase: ports 55321 (API)/55322 (DB)/55323 (Studio)/55324 (Inbucket)/55327 (Analytics) — NOT 54321 default (D-004). Wait for `(healthy)` after any `db reset` before hitting Storage.
- `.env`: real ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY, DATABASE_URL. Never print/log/commit.
- Schema: 11 tables (8 core + `analyses` + `documents.clauses`). New `public` tables need `GRANT ... TO service_role` (D-005).
- `supabase/seed.sql`: demo user + 3 deals (Deal A, Horizon Freight Corp, Nova Fintech). Deal A has real uploaded documents/contracts + analyses from Phase 2/3 testing — good real data for Deal Detail screens.
- Backend routes: `/health`, `/deals` (CRUD), `/deals/{id}/documents`, `/deals/{id}/analyze`, `/contracts`, `/deals/{id}/ask`, `/chat` (WebSocket). `sys.path` self-bootstraps (D-009).
- Agents: every node wraps its FULL body in `with_retry` (D-008/D-010). `agents/deal_context.py` structurally enforces deal_id scoping — never weaken this.
- `/chat` is request/response, not streaming (D-012).
- Frontend so far: no router — single App.tsx with Dashboard (Board/Kanban) + Chat panel. This phase adds react-router + a real app shell (top bar + sidebar) per ux-ui-spec.md Section 2.1, since multiple real screens are being built now.
