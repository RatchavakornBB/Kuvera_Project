## Current
Phase 6 (post-5-day-plan extension) is fully complete (see prior entries below). Phase 7 has now
started: user reported the Chat page "didn't exist" and provided a reference screenshot of a
full-page NotebookLM-style Chat interface (Sources panel, mode tabs), which doesn't match
ux-ui-spec.md 3.3's written "slide-out panel" spec. Clarified scope first (the mockup's Sources
list implied multi-deal selection, which conflicts with the deal_id scoping invariant), then built
phase7-001: a real dedicated /chat page + /today + /daily-digest pages, all reusing existing real
backend endpoints, no fabricated data or fake RBAC.
Active task: none (phase7-001 complete)
Status: idle
Last checkpoint commit: 5cb82d1
Blocked on: nothing

## Next up
Nothing queued. If the user wants further work, check PROCESS/backlog.md's Done section for full
history first, and docs/demo-script.md for the current honest Live vs. Design-only state.
phase7-001 replaced the old slide-out ChatPanel.tsx (now deleted) with a real routed /chat page:
Sources panel (real fetchDeals(), single-select — NOT multi-deal, per explicit user confirmation
that the deal_id scoping invariant stays intact), 4 cosmetic mode tabs (Concierge/Analyst/
Contracts/Drafting — placeholder/color only, real Orchestrator still does the actual routing on
every message). Added /today (real needs-attention deals + real key dates) and /daily-digest
(wraps the existing real LearningAgentTab). Added a non-interactive "View as: Owner" badge —
deliberately NOT wired to fake RBAC, since none exists. Sidebar reordered to Today/Dashboard/Chat/
Documents & Contracts/Daily Digest/Agent Hub/Admin; deliberately did NOT add a separate "Deals"
nav item since Dashboard already is the deals list. useChatSocket() still lives in AppShell so
message history persists across navigation.
phase6-009 audited every backend route against every frontend api.ts caller in both directions —
zero orphaned api.ts exports; two legitimate non-connections confirmed intentional (`/deals/{id}/ask`
superseded by `/chat`, `/documents/backfill-embeddings` is maintenance-only); one real gap found
and fixed (`POST /contracts` had no UI — added the "This is a contract" checkbox to
UploadDocumentModal.tsx + uploadContract() in api.ts). Wiring it up immediately caught a real bug:
clause_extractor.py stored a stringified `{"clauses": [...]}` wrapper instead of a real array on
its first-ever live invocation (Claude occasionally returns a JSON string for an array-typed
tool_use field — the exact failure mode agents/knowledge.py's _normalize_field already handles for
object fields, never applied here). Fixed with `_normalize_clauses()`. Confirmed via the seed
Contract doc's clean data that this was a live-pipeline bug, not old corruption — seed.sql bypassed
the buggy path entirely.
phase6-008 built real pgvector search for documents.py (embedding vector(1024) column, reuses
agents/embeddings.py's Voyage AI pipeline — no second embeddings integration). Embed on upload
(filename) + re-embed on summary landing (name+summary), real cosine query replacing the old
Python substring filter. Found and fixed a real bug in backfill_missing_embeddings() hitting the
same per-record-loop 429 anti-pattern documented in agents/embeddings.py — fixed to batch via
embed_texts(). Frontend search input now debounced (400ms) since it drives a real paid API call
per query. Every read path (list_documents/get_document/get_latest_document/upload_document)
uses an explicit DOCUMENT_COLUMNS list — "select *" would have leaked the 1024-float vector into
every API response once the column existed.
phase6-007 built agents/evals.py: real hand-written eval cases for 3 agents (pricing_advisor,
ic_memo_drafter, risk_flagger), real LLM-as-judge grading (a second real Claude call), pass_rate
stored on pending_changes and shown as a real green/red bar (0.7 threshold) in Pending Approvals.
Agents without eval cases report that honestly rather than faking a score.
phase6-006 built a real backend/app/scheduler.py (BackgroundScheduler, wired to FastAPI startup/
shutdown): key_date_check every 5min, industry_brief_refresh every 24h. Learning Agent stays
on-demand deliberately (needs a real topic). Real `scheduled_run_log` table is the audit trail.
phase6-004 fixed a real pre-existing gap: no document download mechanism existed anywhere in the
app before — GET /documents/{id}/download now exists and is wired into every document list.
phase6-005 instrumented call_model() itself with real activity_tracker logging — every agent now
has a real status trail, not just the 4 Analyst Lead nodes.

## Open questions for user
- none currently open

## Environment notes (read before assuming state)
- Local Supabase: ports 55321 (API)/55322 (DB)/55323 (Studio)/55324 (Inbucket)/55327 (Analytics) — NOT 54321 default (D-004). Wait for `(healthy)` after any `db reset` before hitting Storage.
- `.env`: real ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY, DATABASE_URL, VOYAGER_API_KEY (sic —
  not VOYAGE_API_KEY, matches what agents/config.py actually reads). Never print/log/commit.
- Schema: 16 tables (8 core + `analyses` + `documents.clauses` + `agent_configs` +
  `pending_changes` + `audit_log` + `knowledge_base` + `contradictions` + `learning_digests` +
  `agent_invocations` + `scheduled_run_log`; Drafting Lead reuses `documents`, no new table).
  New `public` tables need
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
  `/deals/{id}/contradictions` (+ `/{id}/resolve`), `/admin/learning` (`/run`, `/digests`),
  `/admin/pending-approvals/{id}/run-eval`, `/admin/scheduler/status` + `/runs`,
  `/agent-hub/grid` + `/agents/{name}` + `/graph/analyst-lead`,
  `/deals/{id}/draft/{memo,deck,email,summary}`, `/documents/{id}/download`.
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
- `agents/evals.py`: real eval cases only exist for pricing_advisor, ic_memo_drafter, risk_flagger
  — `run_eval()` returns `pass_rate: None` honestly for any other agent rather than faking a score.
  Grading is a real second Claude call (`_grade()`), not a keyword/string match — don't replace it
  with something cheaper without re-verifying it can still produce a real FAIL.
- `agents/nodes/clause_extractor.py`: `_normalize_clauses()` defends against Claude returning a
  JSON-encoded string (sometimes a redundantly-nested `{"clauses": [...]}`) instead of a raw array
  for the tool_use "clauses" field — found via real live testing in phase6-009, the array-typed
  counterpart to `agents/knowledge.py::_normalize_field`'s object-typed defense. Don't remove this
  thinking it's dead defensive code; it fired on the very first real end-to-end contract upload.
- `backend/app/services/documents.py`: `documents.embedding` (Voyage, same pipeline as
  knowledge_base) is embedded on upload (filename) and re-embedded on summary landing
  (name+summary). Every read path uses the explicit `DOCUMENT_COLUMNS` list, never `select("*")` —
  the embedding column must not leak into an API response. `list_documents(q=...)` now runs real
  pgvector cosine search (`_search_documents`); rows with no embedding are excluded, not ranked
  last — use `POST /documents/backfill-embeddings` (batched via `embed_texts`, never loop
  `embed_text` per row) to catch up any that failed at write time. Frontend search input in
  DocumentsContracts.tsx is debounced 400ms since each query is now a real paid Voyage call.
- `/chat` is request/response, not streaming (D-012).
- Frontend routes (App.tsx): `/` (Dashboard), `/today` (Today), `/chat` (Chat — full page, not a
  toggle panel, since phase7-001), `/deals/:id` (Deal Detail, 4 tabs), `/documents` (Documents &
  Contracts), `/daily-digest` (Daily Digest), `/agent-hub` (Agent Hub), `/admin` (Admin & Skill
  Governance, 5 tabs: Agents & Models, Skills, Pending Approvals, Knowledge Base, Audit Log).
  `useChatSocket()` lives in AppShell (outside the routed Outlet) and is passed down via
  `ShellContext.chat` — this is why message history persists across navigation, not because Chat
  is a panel anymore. TopBar's NotificationBell also lives in AppShell for the same reason.
  `ShellContext` also carries `selectedDeal`/`setSelectedDeal` (the single active chat Source) and
  `askAboutDeal(dealId, dealName)` (sets selectedDeal + navigates to `/chat`).
- Claude Code's auto-mode permission classifier will block raw direct-DB deletes/mutations run via
  Bash that it can't verify are self-created test artifacts, even mid-session — ask the user for
  explicit sign-off before retrying rather than working around it (happened twice this session,
  phase5-004 and again during phase5-009 testing).
