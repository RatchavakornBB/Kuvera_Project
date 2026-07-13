## Current
Phase: 6 (post-5-day-plan extension) — the 5-day plan finished 2026-07-13, then the user
explicitly asked to build Admin & Skill Governance (previously a design-only candidate).
Real-scoped per AskUserQuestion confirmation: Agents & Models + Skills + Pending Approvals +
Audit Log tabs, real DB-backed, wired into the actual call_model() chokepoint. Knowledge Base
tab and eval pass-rate bar explicitly excluded — nothing real backs them (no Knowledge Agent,
no eval framework exist anywhere in this codebase).
Active task: phase5-006-admin-skill-governance (mid-build: migration done, wiring call_model() now)
Status: in_progress
Last checkpoint commit: d0f9254
Blocked on: nothing

## Next up
Finish phase5-006: call_model() DB integration, backend routes, frontend /admin screen, then a
real end-to-end verification (approve a skill change, confirm the next real Claude API call
actually carries it). phase5-007 (cross-deal document isolation fix in /deals/{id}/analyze) is
already done and pushed — found during a user-requested audit of every node's data-access
pattern that led into this task.

## Open questions for user
- none currently open

## Environment notes (read before assuming state)
- Local Supabase: ports 55321 (API)/55322 (DB)/55323 (Studio)/55324 (Inbucket)/55327 (Analytics) — NOT 54321 default (D-004). Wait for `(healthy)` after any `db reset` before hitting Storage.
- `.env`: real ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY, DATABASE_URL. Never print/log/commit.
- Schema: 11 tables (8 core + `analyses` + `documents.clauses`). New `public` tables need `GRANT ... TO service_role` (D-005).
- `supabase/seed.sql`: demo user + 3 deals (Deal A, Horizon Freight Corp, Nova Fintech). Deal A has real uploaded documents/contracts + analyses from Phase 2/3 testing — good real data for Deal Detail screens.
- Backend routes: `/health`, `/deals` (CRUD + `/deals/{id}/tasks`), `/deals/{id}/documents`,
  `/deals/{id}/analyze` + `/deals/{id}/analysis` (GET, hydrate without a fresh LLM run),
  `/documents` (cross-deal), `/contracts`, `/deals/{id}/ask`, `/chat` (WebSocket),
  `/agent-hub/activity`, `/notifications/key-dates`. `sys.path` self-bootstraps (D-009).
- Agents: every node wraps its FULL body in `with_retry` (D-008/D-010). `agents/deal_context.py` structurally enforces deal_id scoping — never weaken this.
- `/chat` is request/response, not streaming (D-012).
- Frontend routes (App.tsx): `/` (Dashboard), `/deals/:id` (Deal Detail, 4 tabs), `/documents`
  (Documents & Contracts), `/agent-hub` (Agent Hub) — all real, all wired to real backend data as
  of Phase 4. TopBar's NotificationBell and the Chat panel both live in AppShell (outside the
  routed Outlet), so their state persists across navigation by design.
- Seed data note for Phase 5 empty-state testing: Horizon Freight Corp and Nova Fintech have much
  sparser data than Deal A (no documents/analyses) — good real cases for verifying empty states,
  don't need to fabricate test fixtures for that.
