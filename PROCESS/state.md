## Current
Phase: 3 (Contracts, Concierge, Chat) — COMPLETE
Active task: none
Status: idle, ready to pull next task
Last checkpoint commit: f3e24bc (phase3-006 not yet committed — next commit)
Blocked on: nothing

## Next up
Nothing pulled yet. backlog.md "Ready" has Phase 4 items (Deal Detail, Documents &
Contracts screen, Agent Hub, Key-date notifier) plus the still-open phase1-007
(Table/Pipeline view) and a Phase 5 admin-screen scope question. Ask the user which
to prioritize.

## Open questions for user
- Whether Admin & Skill Governance should be built or stay design-only (system
  design's MVP scope table doesn't explicitly rule on it) — not asked yet.

## Environment notes (read before assuming state)
- Local Supabase: ports 55321 (API)/55322 (DB)/55323 (Studio)/55324 (Inbucket)/55327 (Analytics) — NOT the 54321 default (D-004). Check `docker ps` before assuming it's up; wait for `(healthy)` after any `db reset` before hitting Storage.
- `.env`: real ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY, DATABASE_URL. Never print/log/commit these.
- Schema: 11 tables now (8 core + `analyses` + `documents.clauses` column added via migration). New `public` tables need `GRANT ... TO service_role` (D-005).
- `supabase/seed.sql`: demo user (demo@kuvera.capital / kuvera-demo) + 3 deals. Seeded `auth.users` needs every `*_token`/`email_change*` column `''` not NULL (D-006).
- Backend routes: `/health`, `/deals` (CRUD), `/deals/{id}/documents` (upload), `/deals/{id}/analyze` (full Analyst Lead graph), `/contracts` (4.1+4.2), `/deals/{id}/ask` (Concierge Q&A), `/chat` (WebSocket — Orchestrator routes to concierge_qa/analyst_lead/web_research). `sys.path` self-bootstraps in main.py (D-009).
- Agents (`agents/`): standalone, own config/db (D-007). Every node MUST wrap its FULL body in `with_retry`, not just the model call (D-008/D-010). `agents/deal_context.py` is how the deal_id scope invariant is enforced STRUCTURALLY (never fetches another deal's rows) — this is the one thing to never weaken. `agents/tools/sec_edgar.py` does real un-keyed SEC API calls; its company-name matching had a real false-positive bug (D-noted in phase3-006 report) fixed via word-boundary matching + a stoplist.
- `/chat` is request/response, NOT token streaming (D-012, deliberate cut-order item).
- Frontend: Dashboard (Board/Kanban) + full Chat panel (real WebSocket, deal-context-aware) both wired to real backend data. Table/Pipeline view, Deal Detail, Documents & Contracts screen, Agent Hub, Admin screens still unbuilt (all still just the mockup + written spec).
