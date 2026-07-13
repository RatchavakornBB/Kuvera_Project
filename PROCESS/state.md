## Current
Phase: 5 (Polish & Rehearsal) — COMPLETE 2026-07-13. The entire 5-day build plan is now done.
Active task: none
Status: idle
Last checkpoint commit: 2252b95
Blocked on: nothing

## Next up
Nothing scheduled. Open backlog items, not pulled in unless the user asks:
phase5-admin-skill-governance (design-only candidate — needs its own user decision), and the
already-itemized Live vs. Design-only gaps in docs/demo-script.md (Drafting Lead,
Knowledge/Learning Agent, RBAC, real pgvector semantic search, full Agent Hub live-graph view,
true scheduled cron for the key-date notifier). Otherwise: awaiting user direction.

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
- Frontend routes (App.tsx): `/` (Dashboard), `/deals/:id` (Deal Detail, 4 tabs), `/documents`
  (Documents & Contracts), `/agent-hub` (Agent Hub) — all real, all wired to real backend data as
  of Phase 4. TopBar's NotificationBell and the Chat panel both live in AppShell (outside the
  routed Outlet), so their state persists across navigation by design.
- Seed data note for Phase 5 empty-state testing: Horizon Freight Corp and Nova Fintech have much
  sparser data than Deal A (no documents/analyses) — good real cases for verifying empty states,
  don't need to fabricate test fixtures for that.
