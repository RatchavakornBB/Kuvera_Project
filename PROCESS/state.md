## Current
Phase 6 (post-5-day-plan extension) is in progress: user asked to build out the remaining
Design-only gaps in this explicit order — [1] Contradiction/Hypothesis engine (done),
[2] Knowledge Agent Industry/Competitor Briefs (done), [3] Learning Agent (done), [4] Drafting
Lead, [5] Agent Hub full view, [6] Key-date notifier true cron, [7] Eval pass-rate bar,
[8] Documents & Contracts semantic search. Proceeding through the list without per-item
re-confirmation per the user's instruction — only stopping to ask when something is a genuine
blocker (e.g. needed a real API key for phase5-009's Voyage embeddings).
Active task: phase6-005-agent-hub-full-view (next in the ordered list)
Status: in_progress
Last checkpoint commit: 6bee881
Blocked on: nothing

## Next up
phase6-005 (Agent Hub full view) through phase6-008 (Documents & Contracts semantic search), in
the order above. Note logged in phase6-002/003's reports: once phase6-006 (Key-date notifier's
real scheduler) exists, retrofit it to also call refresh_industry_brief()/refresh_competitor_brief()
(agents/industry_brief.py) and run_learning_cycle() (agents/learning_agent.py) on a real interval —
right now all three are on-demand only.
phase6-004 also fixed a real pre-existing gap: no document download mechanism existed anywhere in
the app before — GET /documents/{id}/download now exists and is wired into every document list.

## Open questions for user
- none currently open

## Environment notes (read before assuming state)
- Local Supabase: ports 55321 (API)/55322 (DB)/55323 (Studio)/55324 (Inbucket)/55327 (Analytics) — NOT 54321 default (D-004). Wait for `(healthy)` after any `db reset` before hitting Storage.
- `.env`: real ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY, DATABASE_URL, VOYAGER_API_KEY (sic —
  not VOYAGE_API_KEY, matches what agents/config.py actually reads). Never print/log/commit.
- Schema: 16 tables (8 core + `analyses` + `documents.clauses` + `agent_configs` +
  `pending_changes` + `audit_log` + `knowledge_base` + `contradictions` + `learning_digests`;
  Drafting Lead reuses `documents`, no new table). New `public` tables need
  `GRANT ... TO service_role` (D-005). Apply new migrations with `supabase migration up`, never
  `db reset`, once real accumulated test/demo data exists (a reset wipes it).
- `agents/contradictions.py`: real pgvector-matched corroboration (threshold 0.70, calibrated
  against real embeddings — 0.77 for a genuine paraphrase, 0.50 for an unrelated one). Wired into
  risk_flagger via a new `is_contradiction` field on its tool schema. `risk_flagger`'s `max_tokens`
  is now 16384 (raised twice from 4096 after real live runs kept hitting the ceiling — don't lower
  it without re-verifying against a real run). `agents/industry_brief.py`: on-demand Industry/
  Competitor Brief refresh via real web_search, stored in `knowledge_base` with `source_deal_id`
  null.
- `supabase/seed.sql`: demo user + 3 deals (Deal A, Horizon Freight Corp — has one test image
  document from phase5-008/phase5-007 testing, Nova Fintech — now `status: Closed` with 8 real
  promoted `knowledge_base` records from phase5-009 testing). Deal A has real uploaded
  documents/contracts + analyses from Phase 2/3 testing.
- Backend routes: `/health`, `/deals` (CRUD + `/deals/{id}/tasks` + `/deals/{id}/close`),
  `/deals/{id}/documents`, `/deals/{id}/analyze` + `/deals/{id}/analysis` (GET), `/documents`
  (cross-deal), `/contracts`, `/deals/{id}/ask`, `/chat` (WebSocket), `/agent-hub/activity`,
  `/notifications/key-dates`, `/admin/agents` + `/admin/agents/{name}/propose` +
  `/admin/pending-approvals` (+ `/approve` / `/reject`) + `/admin/audit-log`,
  `/admin/knowledge-base` (+ `/search`, `/refresh-industry-brief`, `/refresh-competitor-brief`),
  `/deals/{id}/contradictions` (+ `/{id}/resolve`), `/admin/learning` (`/run`, `/digests`).
  `sys.path` self-bootstraps (D-009). Verified: mixing Claude's `web_search` server tool with a
  custom structured-output tool in one call works (agents/learning_agent.py) — untested before
  phase6-003, don't assume it doesn't work if reconsidering agents/industry_brief.py's
  freeform-text-only design.
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
