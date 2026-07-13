## Current
Phase: 6 (post-5-day-plan extension) — COMPLETE 2026-07-13. Since the 5-day plan finished, the
user asked for three more real features, all built and verified: phase5-006 (Admin & Skill
Governance, real-scoped), phase5-007 (fixed a real cross-deal document isolation bug found during
a requested audit), phase5-008 (real image file support for document-reading nodes), phase5-009
(full Knowledge Agent incl. real pgvector semantic search via Voyage AI). docs/demo-script.md is
current as of the last commit below.
Active task: none
Status: idle
Last checkpoint commit: 648a920
Blocked on: nothing

## Next up
Nothing scheduled. Open backlog items, not pulled in unless the user asks: phase5-admin-skill-
governance's Knowledge Base tab is now done, but eval pass-rate scoring is still not built (no
eval framework exists). Remaining Design-only gaps per docs/demo-script.md's Live vs. Design-only
table: Drafting Lead, Learning Agent (continuous outside-world ingestion — distinct from the now-
live Knowledge Agent), Industry/Competitor/Company Insight within the Knowledge Agent (need a
periodic cross-deal Brief pipeline), RBAC, Documents & Contracts screen's substring-only search
(the Knowledge Base's search is real pgvector; that one specific screen's search bar was never
upgraded), full Agent Hub live-graph view, true scheduled cron for the key-date notifier. Otherwise
awaiting user direction.

## Open questions for user
- none currently open

## Environment notes (read before assuming state)
- Local Supabase: ports 55321 (API)/55322 (DB)/55323 (Studio)/55324 (Inbucket)/55327 (Analytics) — NOT 54321 default (D-004). Wait for `(healthy)` after any `db reset` before hitting Storage.
- `.env`: real ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY, DATABASE_URL, VOYAGER_API_KEY (sic —
  not VOYAGE_API_KEY, matches what agents/config.py actually reads). Never print/log/commit.
- Schema: 14 tables (8 core + `analyses` + `documents.clauses` + `agent_configs` +
  `pending_changes` + `audit_log` + `knowledge_base`). New `public` tables need
  `GRANT ... TO service_role` (D-005). Apply new migrations with `supabase migration up`, never
  `db reset`, once real accumulated test/demo data exists (a reset wipes it).
- `supabase/seed.sql`: demo user + 3 deals (Deal A, Horizon Freight Corp — has one test image
  document from phase5-008/phase5-007 testing, Nova Fintech — now `status: Closed` with 8 real
  promoted `knowledge_base` records from phase5-009 testing). Deal A has real uploaded
  documents/contracts + analyses from Phase 2/3 testing.
- Backend routes: `/health`, `/deals` (CRUD + `/deals/{id}/tasks` + `/deals/{id}/close`),
  `/deals/{id}/documents`, `/deals/{id}/analyze` + `/deals/{id}/analysis` (GET), `/documents`
  (cross-deal), `/contracts`, `/deals/{id}/ask`, `/chat` (WebSocket), `/agent-hub/activity`,
  `/notifications/key-dates`, `/admin/agents` + `/admin/agents/{name}/propose` +
  `/admin/pending-approvals` (+ `/approve` / `/reject`) + `/admin/audit-log`,
  `/admin/knowledge-base` (+ `/search`). `sys.path` self-bootstraps (D-009).
- Agents: every node wraps its FULL body in `with_retry` (D-008/D-010). `agents/deal_context.py`
  structurally enforces deal_id scoping — never weaken this. `call_model()`
  (agents/adapters/model_adapter.py) now reads real DB-backed model_id/skill_content from
  `agent_configs` on every call — the Admin & Skill Governance chokepoint, never bypass it.
  `agents/documents.py::build_content_block()` is the one place a document's bytes become a
  Claude content block (PDF -> `document`, image -> `image`) — every document-reading node uses
  it, don't hardcode block shapes in a node again. `agents/knowledge.py` is the Knowledge Agent:
  `promote_deal_to_knowledge()` (real Claude synthesis + real Voyage embeddings, called from
  `POST /deals/{id}/close`) and `search_knowledge()` / `historical_precedent_context()` (real
  pgvector cosine search, the latter used inside risk_flagger/pricing_advisor, best-effort/
  swallows its own failures since it's supplementary context).
- `/chat` is request/response, not streaming (D-012).
- Frontend routes (App.tsx): `/` (Dashboard), `/deals/:id` (Deal Detail, 4 tabs), `/documents`
  (Documents & Contracts), `/agent-hub` (Agent Hub), `/admin` (Admin & Skill Governance, 5 tabs:
  Agents & Models, Skills, Pending Approvals, Knowledge Base, Audit Log). TopBar's
  NotificationBell and the Chat panel both live in AppShell (outside the routed Outlet), so their
  state persists across navigation by design.
- Claude Code's auto-mode permission classifier will block raw direct-DB deletes/mutations run via
  Bash that it can't verify are self-created test artifacts, even mid-session — ask the user for
  explicit sign-off before retrying rather than working around it (happened twice this session,
  phase5-004 and again during phase5-009 testing).
