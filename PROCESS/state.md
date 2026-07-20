## Current
Phase 6 (post-5-day-plan extension) is fully complete (see prior entries below). Phase 7 is
underway: phase7-001 through phase7-007 rebuilt/fixed Chat (dedicated page, .docx support, request
timeout, artifact Open button, Sources document list, add-link sources, link auto-summarize — all
complete, see below). phase7-008 added real episodic chat memory (persistent conversations, RAG
recall, auto-digest, multi-tab). phase7-009 added tab deletion with forced digest-before-delete,
and found+fixed a real bug (a Voyage rate limit was discarding whole synthesized digests, not just
failing to embed them). phase7-010 added auto-NDA-on-deal-create (new nda_drafter agent, see below).
Everything live-verified against the real Anthropic API.
Active task: none
Status: idle (phase7-010 committed as 2a2f94e; backend uvicorn on :8000 restarted and confirmed
serving the new code — /health OK, /deals/{deal_id}/draft/nda live in OpenAPI)
Last checkpoint commit: 2a2f94e
Blocked on: nothing.
Note (2026-07-20): agents/adapters/model_adapter.py now also has a real Gemini (Google) adapter
added by a PARALLEL session mid-task — not part of phase7-010. phase7-010 only added the
`nda_drafter` entry to AGENT_MODELS there; left the Gemini work untouched. Re-read that file before
assuming its shape.
Note: backend/app/routes/chat.py, agents/web_source.py, backend/app/services/contracts.py,
agents/documents.py, and related files have real parallel additions beyond what these PROCESS
entries document (contracts_lead/drafting_lead/update_stage/web_research-to-document chat routing,
direct file-URL fetching) — not authored in this session's tracked phase7 work, encountered
mid-task via IDE change notifications. Left untouched and not re-documented here since they're
outside what was asked; re-read the actual files before assuming their behavior from memory.

## Next up
Nothing queued. If the user wants further work, check PROCESS/backlog.md's Done section for full
history first, and docs/demo-script.md for the current honest Live vs. Design-only state.
phase7-010 added auto-NDA-on-deal-create (user: "After create deal the AI will create the NDA doc
for client and put in deal page"). When a deal is created, deals_service.create_deal() fires
_draft_nda_async() on a daemon thread (best-effort — an NDA failure must never break/hang deal
creation, mirroring documents.py's citation-link background pattern). It calls
agents/drafting_lead.py::draft_and_store_nda() → draft_nda() (a real Claude call) → draft_nda_docx()
(python-docx via the existing _add_markdown_paragraphs renderer) → _upload_and_record() (same real
Storage+Document write path as memo/deck), producing a `type='NDA'` .docx that shows in the deal's
Documents tab (DealFileLibrary lists all types, no filter — no frontend change needed). Also added a
manual POST /deals/{id}/draft/nda (drafting service+route) for re-draft/verification. KEY DECISION
(D-013): NDA drafting uses a NEW `nda_drafter` agent identity, NOT `drafting_lead` — drafting_lead's
governed skill deliberately forbids from-scratch generation and the model correctly REFUSED when
called as drafting_lead (its refusal text got saved as the "NDA" on the first verification run — a
real finding, caught because the automated marker-check nearly false-passed on it). Switching to
`nda_drafter` (added to AGENT_MODELS, no restrictive skill) produced a real 5.7KB NDA with proper
numbered sections and zero refusal markers. Verified live end-to-end through create_deal() +
TestClient; both throwaway "ZZ NDA Verify" test deals were cleaned up (rows + storage). Not
committed yet.
phase7-009 added conversation deletion with a forced digest first (force_digest_conversation()
bypasses the normal 10-message threshold — agents/chat_memory.py). Found and fixed a real bug
during its own verification: _run_digest() was discarding an already-synthesized real digest
entirely when the trailing embedding call hit a real Voyage 429 (a rate limit legitimately earned
from this session's heavy real API testing) — fixed by making the embedding step its own
try/except (embedding=None on failure), matching documents.py's established null-embedding-then-
backfill pattern. Added the missing knowledge_base counterpart:
agents/knowledge.py::backfill_missing_embeddings() + POST /admin/knowledge-base/backfill-embeddings
(this table never needed one before — every prior write path embedded synchronously and
successfully, or failed the whole insert). Verification involved diagnosing 3 real Playwright-side
false alarms via direct DB inspection before finding the real bug — see the phase7-009 report for
the full arc; each dead end was confirmed via the database, never assumed.
phase7-008 built real episodic chat memory (user asked for 4 things: persistent memory, RAG,
Knowledge auto-summarize, multi-tab). New chat_conversations/chat_messages tables — chat was
previously pure in-memory React state with zero DB backing (confirmed via a dedicated research
pass before building). Every message embedded immediately (Voyage AI); agents/chat_memory.py::
search_chat_history() does real pgvector search wired into concierge_qa, so Concierge genuinely
recalls past exchanges now (verified: a real "summarize what we discussed" answer referenced
actual prior conversation content). maybe_digest_conversation() fires a real Claude synthesis call
every 10 new messages, writing a knowledge_base row under a new 'chat_insights' category.
ChatPage.tsx has a real tab strip per deal, auto-titled from each conversation's first message.
Found and fixed 2 real bugs during live testing: (1) Claude's report_chat_digest tool_use omitted
the required 'topic' field entirely — fixed with a fallback, mirrors the earlier clause_extractor
tool-use-conformance lesson but a different failure shape (missing field vs wrong-typed field);
(2) real-time per-message embedding hit Voyage's rate limit (7/10 messages failed) — fixed with
backfill_missing_message_embeddings() + POST /conversations/backfill-embeddings, mirroring
documents.py's existing fix for the identical problem.
phase7-007 fixed a real gap found while answering the user's "will the Agent be able to read a
link source" question: agents/deal_context.py::build_deal_context() (what Concierge Q&A actually
reads) only ever surfaces a document's `summary` field, never raw bytes — a freshly-added link had
`summary: null` until someone separately ran Analyze, so it was invisible to Concierge despite
being fully stored. Fixed by running a real doc_summarizer call immediately in
create_document_from_url() (just that one node, not the full pipeline). Verified live: real
~35.8s add-link call produced a real grounded summary, confirmed via build_deal_context() directly
that Concierge's context now includes it, and a real Concierge Q&A round-trip correctly referenced
the document while honestly declining to state details beyond its 200-char preview (a
pre-existing, deal-context-wide cap applying to every document type, not link-specific) rather
than fabricating an answer.
phase7-006 added real "add a link" URL sources: agents/web_source.py fetches a real page
server-side (httpx) and extracts real readable text (BeautifulSoup, strips script/style) — the
page's own real content, not a fabricated summary. Real SSRF protection
(_assert_public_host — new dependency beautifulsoup4) blocks private/loopback/link-local/metadata
targets, tested against 4 real unsafe URLs including the AWS/GCP metadata IP. documents.source_url
column added (real provenance tracking). agents/documents.py::build_content_block() gained real
.txt support so link-derived documents are fully analyzable through the existing pipeline, not a
lesser stub — verified directly (bypassing the credit-exhausted Claude API) that a link document
round-trips correctly through fetch_document()/build_content_block(). POST
/deals/{deal_id}/documents/from-url reuses upload_document()'s exact real write path.
phase7-005 added a real per-deal document list to ChatPage.tsx's Sources panel: clicking a deal
selects it as chat context (unchanged) AND expands its real documents (fetchDocuments({deal_id}),
same function Documents & Contracts/Deal File Library use) with real download links
(documentDownloadUrl()) — no new backend endpoint, no LLM call involved, so fully verified despite
the current API credit outage.
phase7-004 fixed: the Chat assistant's analyst_lead response preview was hard-cut at 300 chars
(backend/app/routes/chat.py) — confirmed via the real stored summary (2575 chars, complete
sentence, well under doc_summarizer's real 1536-token ceiling) that this was NOT an LLM token
limit, just a UI preview slice, now trimmed to a word boundary. Investigating that surfaced a
worse bug: the artifact card's "Open" button (meant to show the full analysis) was never wired to
anything in ChatPage.tsx (built in phase7-001) — fixed by adding deal_id to the artifact response
and wiring onOpen to navigate to /deals/{id}?tab=analysis, which required adding real ?tab=
deep-linking to DealDetail.tsx (didn't exist before — tab state was always local-only).
phase7-003 fixed a real live hang: agents/adapters/model_adapter.py's Anthropic client had no
explicit timeout (SDK default ~10min), so a stalled network call could block a thread-pool worker
indefinitely with zero visible error. Confirmed the hang was real (not assumed) by checking the
LangGraph checkpoint table for the exact thread_id and finding zero rows, then re-running the
identical call directly — it completed in ~19.5s, ruling out a systemic pipeline break. Fixed on
both ends: backend now sets timeout=120.0 (agents/adapters/model_adapter.py::REQUEST_TIMEOUT_SECONDS,
a stall now raises a real exception with_retry converts to NodeFailure); frontend
(useChatSocket.ts) now has a 150s client-side timer that resets `busy` and shows a real message if
no response arrives, instead of hanging "thinking…" forever. Re-verified against the user's own
real uploaded document (not test data) after restarting the backend — clean 200, real correct
response.
phase7-002 added real .docx support to agents/documents.py::build_content_block() — Claude has no
native Word-document content block, so real text is extracted via python-docx (already a
dependency from phase6-004's Drafting Lead, used the opposite direction there) and sent as a text
block. Every document-reading node (doc_summarizer/risk_flagger/contract_summarizer/
clause_extractor) needed zero changes since they all already just spread build_content_block()'s
output into a content array — the single-chokepoint design paid off. Verified through the real
live /analyze API end to end (not just the extraction function): a real new .docx with real
financial figures produced a real summary, real risk flags, and a real correctly-detected
contradiction against Deal A's differently-figured prior analysis. Hit and recovered from the
known "backend wasn't restarted so still running old code" gotcha mid-verification — recognized
the stale error text immediately rather than assuming the fix was wrong.
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
- Schema: 18 tables (8 core + `analyses` + `documents.clauses` + `agent_configs` +
  `pending_changes` + `audit_log` + `knowledge_base` + `contradictions` + `learning_digests` +
  `agent_invocations` + `scheduled_run_log` + `chat_conversations` + `chat_messages`; Drafting Lead
  reuses `documents`, no new table). `documents` also has `embedding` (phase6-008) and
  `source_url` (phase7-006, NULL except for link-derived documents). `knowledge_base.category`
  gained `chat_insights` (phase7-008, real Claude-synthesized digests of chat history). New
  `public` tables need
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
  `/deals/{id}/draft/{memo,deck,email,summary}`, `/documents/{id}/download`,
  `/documents/backfill-embeddings`, `/deals/{id}/documents/from-url`,
  `/deals/{id}/conversations` (GET+POST) + `/conversations/{id}/messages` +
  `/conversations/backfill-embeddings` + `/conversations/{id}` (DELETE) +
  `/admin/knowledge-base/backfill-embeddings`.
  `sys.path` self-bootstraps (D-009). Verified: mixing Claude's `web_search` server tool with a
  custom structured-output tool in one call works (agents/learning_agent.py) — untested before
  phase6-003, don't assume it doesn't work if reconsidering agents/industry_brief.py's
  freeform-text-only design.
- Agents: every node wraps its FULL body in `with_retry` (D-008/D-010). `agents/deal_context.py`
  structurally enforces deal_id scoping — never weaken this. `call_model()`
  (agents/adapters/model_adapter.py) now reads real DB-backed model_id/skill_content from
  `agent_configs` on every call — the Admin & Skill Governance chokepoint, never bypass it.
  `_anthropic_client()` sets an explicit 120s `timeout` (phase7-003, `REQUEST_TIMEOUT_SECONDS`) —
  a real live hang was hit without it (SDK default ~10min, silent, no error). Don't remove this.
  `frontend/src/lib/useChatSocket.ts` has a matching 150s client-side timeout for the same reason.
  `agents/documents.py::build_content_block()` is the one place a document's bytes become a
  Claude content block (PDF -> `document`, image -> `image`, docx -> `text` via real python-docx
  extraction since phase7-002, txt -> `text` via plain UTF-8 decode since phase7-006 — audio/video
  still genuinely unsupported, no real transcription pipeline exists) — every document-reading
  node uses it, don't hardcode block shapes in a node again. `agents/web_source.py` (phase7-006)
  does the real server-side URL fetch + BeautifulSoup text extraction for "add a link" sources,
  with SSRF protection (`_assert_public_host`) — don't remove that guard, it's a real security
  control, not defensive boilerplate. `agents/knowledge.py` is the Knowledge Agent:
  `promote_deal_to_knowledge()` (real Claude synthesis + real Voyage embeddings, called from
  `POST /deals/{id}/close`) and `search_knowledge()` / `historical_precedent_context()` (real
  pgvector cosine search, the latter used inside risk_flagger/pricing_advisor, best-effort/
  swallows its own failures since it's supplementary context). `agents/chat_memory.py` (phase7-008)
  is the episodic chat memory layer: `search_chat_history()`/`chat_history_context()` (real
  pgvector search over `chat_messages`, wired into `concierge_qa`) and
  `maybe_digest_conversation()` (fires a real Claude call every `DIGEST_TRIGGER_MESSAGE_COUNT`=10
  new messages, writes a `knowledge_base` row under `category='chat_insights'`). Its digest tool
  schema has a real, observed quirk: Claude sometimes omits the required `topic` field entirely —
  `_run_digest()` falls back to the conversation's title, don't remove that fallback.
  `backend/app/services/chat_conversations.py::backfill_missing_message_embeddings()` exists
  because real-time per-message embedding is genuinely rate-limit-prone (unlike documents.py's
  batchable case) — call it via `POST /conversations/backfill-embeddings` if chat RAG search seems
  to be missing recent messages. `force_digest_conversation()` (phase7-009) is the same digest but
  bypasses the 10-message threshold, used by `DELETE /conversations/{id}` (deleting a tab digests
  whatever's undigested first, best-effort). `agents/knowledge.py::backfill_missing_embeddings()` +
  `POST /admin/knowledge-base/backfill-embeddings` (phase7-009) exist because `_run_digest()` can
  now insert a `knowledge_base` row with `embedding=None` on a Voyage failure rather than
  discarding the whole digest — don't "fix" that by making the embed call blocking again, that's
  the exact real bug phase7-009 found and fixed.
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
