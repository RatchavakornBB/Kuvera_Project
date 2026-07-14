# PROCESS/backlog.md — ready / blocked / deferred work

## Ready
- (none currently open)

## Blocked
- (none — the Anthropic API credit outage hit live 2026-07-14 that
  blocked phase7-004's remaining verification item was resolved the same
  day when the user topped up the account; the check was re-run and
  passed, see phase7-004 in Done below)

## Explicitly skipped (a decision, not an oversight)
- Cloud deploy (5day-build-timeline.md's optional 15:30-17:00 Phase 5 block) — user confirmed
  local + screen-share is sufficient for the interview (2026-07-13). Revisit only if the user
  later wants a shareable URL.

## Deferred (found mid-task, not in that task's scope)
- (none)

## Minor polish (accepted, not a functional bug)
- (none currently open — the Kanban scroll-affordance gap logged here in Phase 1 was fixed in
  phase5-002, see Done below)

## Done (Phases 1-3, for reference — see PROCESS/reports/ for full detail)
Phase 1 (Foundations): environment setup, 8-table schema, seed data, design tokens,
StageDiagram, DealCard/Kanban, Dashboard wired to real /deals data.

Phase 2 (Core AI Loop): /deals CRUD, document upload -> Storage, call_model() adapter,
3.1 doc_summarizer, 3.2 risk_flagger + contradiction check, 3.3 ic_memo_drafter,
3.4 pricing_advisor, compiled LangGraph (gate + Send() fan-out) with Postgres
Checkpointer, /deals/{id}/analyze wired end to end and verified over real HTTP.

Phase 3 (Contracts, Concierge, Chat): 4.1 contract_summarizer + 4.2 clause_extractor
+ /contracts endpoint, Concierge Q&A with structurally-enforced deal_id scoping
(agents/deal_context.py — the AGENT.md Section 11 invariant), full Chat panel
frontend (message thread, artifact cards, composer, deal-context chip), Orchestrator
LLM-based routing (concierge_qa / analyst_lead / web_research) + /chat WebSocket
(request/response, not streaming — D-012), and web_search + SEC EDGAR tools on the
Analyst Lead, verified end to end via real WebSocket round trips including a real
bug found and fixed (EDGAR company-name matching false positive).

Phase 4 (in progress): app-shell-routing (react-router + top bar/sidebar shell),
phase1-007-table-pipeline-view (Table view + Pipeline funnel strip + New Deal modal,
plus fixing the previously-deferred hardcoded risk_flags=0 now that real risk_flagger
data exists), phase4-001a-deal-detail-overview, phase4-001b-documents-tab (required
docs checklist + file library wired to real upload), phase4-001c-analysis-tab (risk
flag cards grouped by severity, IC memo panel with Regenerate, collapsed pricing
section, new GET /deals/{id}/analysis endpoint to hydrate without a fresh LLM run),
phase4-001d-tasks-notes-tab (task list with quick-add/done-toggle backed by new
POST/PATCH /deals/{id}/tasks, chronological meeting notes feed). Deal Detail's all
4 tabs (Overview/Documents/Analysis/Tasks & Notes) are now complete.

phase4-002-documents-contracts-screen — cross-deal Documents & Contracts screen: new
GET /documents (deal_id/type/status/q filters, joined with owning deal), document
table with 30-day key-date countdown badges, detail side panel with real extracted
clauses, upload modal reusing the existing real upload path, key-dates banner.
Deviation: substring search, not real pgvector semantic search (no embeddings
pipeline exists in this MVP); no approval-status change history (no audit-log table).

phase4-003-agent-hub — static activity log reading the real LangGraph Postgres
Checkpointer state (not the full live-graph/21-agent-grid surface, per the
timeline's own scoped-down instruction). Found and fixed a real bug: the
parallel fan-out step writes two nodes into one checkpoint row, and the first
pass only surfaced one of them.

phase4-004-key-date-notifier — on-demand GET /notifications/key-dates (no
task-queue infra in this MVP, so not a true scheduled job — logged as a
deliberate decision) + a persistent NotificationBell in TopBar, visible on
every screen, with real badge count and localStorage-backed per-item dismiss.

phase4-005-full-integration-pass — one continuous real-browser session across
the whole demo path (Dashboard views -> Deal Detail all 4 tabs -> Chat ->
Documents & Contracts -> Agent Hub -> back). No breakage found; zero console
errors. Phase 4 (Integration) is now complete.

Phase 5 (Polish & Rehearsal) — phase5-001 (real bug found and fixed: CSS
@import order; verified every empty state against real sparse-data deals),
phase5-002 (Kanban scroll-affordance fade, real scroll tracking), phase5-003
(docs/demo-script.md — click path, Live vs. Design-only table, rehearsed
Q&A), phase5-004 (real timed Playwright rehearsal of the full script, 9.5s
total mechanical time), phase5-005 (cloud deploy explicitly skipped per user
decision). The full 5-day build plan is now complete.

Phase 6 (post-5-day-plan extension, user-requested) — phase5-007 (fixed a real
cross-deal document isolation gap in /deals/{id}/analyze, found during a
requested audit of every node's data-access pattern), phase5-006 (Admin &
Skill Governance, real-scoped: Agents & Models / Skills / Pending Approvals /
Audit Log, all DB-backed and wired into the real call_model() chokepoint,
verified by approving a real skill change and confirming it changed a real
Claude API call), phase5-008 (real image file support for the 4 document-
reading nodes via Claude's native `image` content block, verified with a real
generated test image; audio/video deliberately left unsupported — no native
Claude content block for either), phase5-009 (full Knowledge Agent including
real pgvector semantic search via Voyage AI embeddings — a real "Close Deal"
action promotes actual deal data via a real Claude synthesis call,
risk_flagger/pricing_advisor retrieve real historical precedent automatically,
Admin's Knowledge Base tab is real and searchable; Industry/Competitor/Company
Insight deliberately not populated at that point — need a periodic
cross-deal Brief pipeline this MVP doesn't have).

phase6-001-contradiction-engine — full Contradiction/Hypothesis
confidence-scoring engine (no detailed spec exists for this anywhere in
the docs, designed from a one-line description in 5day-build-timeline.md):
real status ranks + real pgvector-matched corroboration counting (0.70
threshold, calibrated against real embeddings) on top of the
already-working lightweight flag, real versioned promotion into the
Knowledge Agent on resolve. Found and fixed a real risk_flagger
max_tokens ceiling (4096 -> 8192 -> 16384) via repeated real
live-pipeline failures, not guessed at once.

phase6-002-industry-competitor-briefs — extends the Knowledge Agent to
Industry/Competitor Insight via real Claude web_search research (reuses
knowledge_base, no new table). On-demand for now — flagged to retrofit
into phase6-006's Key-date notifier scheduler once that's built.

phase6-003-learning-agent — real outside-world research (verified
Claude's web_search server tool can be mixed with a custom
structured-output tool in one call, untested before this) that can
propose real skill.md additions into the exact same pending_changes
approval queue a human uses via the Skills tab. Verified with a real
Thailand PDPA regulatory research cycle that correctly proposed a
specific, grounded addition to risk_flagger's skill.

phase6-004-drafting-lead — real .docx/.pptx generation (python-docx/
python-pptx, new dependencies) from a deal's real stored analysis, plus
a real cover email draft and a NotebookLM-style source-cited summary
built from real risk_flags source_excerpts. Found and fixed a real
pre-existing gap along the way: no document download mechanism existed
anywhere in the app — added a real backend-mediated
GET /documents/{id}/download and wired it into every document list.

phase6-005-agent-hub-full-view — real Agent Grid (13 real agents across
7 Leads, not padded to the spec's "21"), Live Graph (real SVG of
agents/graph.py's actual structure, polls every 3s), agent detail
panel (real sparkline + history). Closed a real gap first: instrumented
call_model() to log every real invocation (agent_invocations table) so
all 13 agents get real status, not just the 4 Analyst Lead nodes the
older checkpoint-based log could see.

phase6-006-key-date-scheduler — real backend/app/scheduler.py
(BackgroundScheduler wired to FastAPI startup/shutdown): key-date
checks every 5min, Industry Brief refresh every 24h. Verified past
"the endpoint works" to the actual timer mechanism (an isolated
scheduler instance fired 4 real times in 9s). Closes the "on-demand,
not a cron" deviation from phase4-004/phase6-002. Also found and fixed
two stale demo-script.md entries (Agent Hub, Learning Agent) still
describing pre-phase6-003/005 state.

phase6-007-eval-framework — real minimal eval framework (agents/evals.py):
hand-written eval cases for 3 agents (pricing_advisor, ic_memo_drafter,
risk_flagger), real LLM-as-judge grading (a second real Claude call),
real on-demand pass-rate bar in Pending Approvals. Proved the grader can
actually fail (direct FAIL-proof against an unsatisfiable criteria) and
found a genuine model-robustness result during adversarial-skill
testing. Found and fixed four more stale demo-script.md rows (Knowledge
Agent's Industry/Competitor Insight, Learning Agent, Drafting Lead,
contradiction engine) while re-reading the whole Live-vs-Design-only
table.

phase6-008-documents-semantic-search — real pgvector cosine search for
the Documents & Contracts screen, reusing knowledge_base's exact Voyage
AI pipeline (documents.embedding vector(1024)). Embedded on upload
(filename) and re-embedded once a real summary lands. Found and fixed a
real bug: backfill_missing_embeddings() initially hit the same
per-record-loop 429 anti-pattern already documented in
agents/embeddings.py (and hit for real in phase5-009) — fixed to batch
via embed_texts(). Verified the failure mode degrades gracefully under
a real rate limit hit mid-`/deals/{id}/analyze` run, then recovers via
the fixed backfill. Also fixed a response leak (every select("*") read
path would have returned the raw embedding vector) and debounced the
frontend search input (400ms) since it now drives a real paid API call
per query.

This closes the last item in the user's ordered phase 6 list.

phase6-009-fullstack-connectivity-audit — user-requested audit
cross-referencing every backend route against every frontend api.ts
caller in both directions. Zero orphaned api.ts exports. Found and
fixed one real gap: POST /contracts (the 4.1/4.2 Contracts Lead
pipeline) had no frontend caller anywhere — the only Contract-type
document in the system was hand-seeded, never produced by a real user
action. Wired up a "This is a contract" checkbox in
UploadDocumentModal.tsx, which immediately caught a real,
previously-latent bug: clause_extractor.py stored a stringified
{"clauses": [...]} wrapper instead of a real array on its first-ever
live invocation. Fixed with _normalize_clauses(), mirroring
agents/knowledge.py's existing defense for the same class of Claude
tool_use quirk. Confirmed via the seed data's clean clauses column
that this was a live-pipeline bug the seed data had simply never
exercised, not old corruption.

Phase 6 (post-5-day-plan extension) is now complete, including this
connectivity pass.

Phase 7 (post-Phase-6, user-requested UI redesign) —

phase7-001-chat-page-redesign — user reported the Chat page "didn't
exist" and shared a reference screenshot of a full-page NotebookLM-
style layout (Sources panel, mode tabs) that doesn't match
ux-ui-spec.md 3.3's written "slide-out panel" spec. Asked clarifying
questions before building since the mockup's Sources list implied
multi-deal selection, conflicting with the deal_id scoping invariant
(agents/deal_context.py). User confirmed: single-deal selection only,
mode tabs are cosmetic (no backend routing change), build the rest of
the mockup too. Built a real /chat page (Sources = real fetchDeals(),
single-select), /today (real needs-attention deals + real key dates),
/daily-digest (wraps the existing real LearningAgentTab), and a
non-interactive "View as: Owner" badge (no fake RBAC — none exists).
Deliberately did not add a redundant "Deals" nav item since Dashboard
already is the deals list. Removed the now-dead ChatPanel.tsx.
Verified a real WebSocket round-trip correctly proved the single-deal
invariant survived the rework: asking "What deals are in the
portfolio?" with Deal A selected as the Source produced a real refusal
to see beyond that one deal.

phase7-002-docx-document-support — user asked if files could support
.docx. Added real text extraction via python-docx (already a
dependency from Drafting Lead) to agents/documents.py's single
content-block chokepoint, so every document-reading node gained
support with zero per-node changes. Verified through the real live
/deals/{id}/analyze API twice: once against a pre-existing real .docx,
once against a brand-new one with specific real financial figures —
got back a real summary, real risk flags, and a real correctly-
detected contradiction against Deal A's differently-figured prior
analysis. Hit and recovered from the known "backend needs a restart to
pick up code changes" gotcha mid-verification. Audio/video remain
genuinely unsupported — no real transcription pipeline exists to
bridge them honestly.

phase7-003-request-timeout-fix — user hit a real live hang: the Chat
assistant stuck "thinking…" for 5+ minutes with no error. Confirmed
via the LangGraph checkpoint table (zero rows for that thread_id —
proof the run never progressed) rather than assuming, then re-ran the
identical call directly and it completed in ~19.5s, ruling out a
systemic break. Root cause: no explicit timeout on the Anthropic
client (SDK default ~10min, silent). Fixed both ends: backend
timeout=120.0 (agents/adapters/model_adapter.py), frontend 150s
client-side timeout (useChatSocket.ts) that surfaces a real message
instead of hanging indefinitely. Re-verified against the user's own
real uploaded document after restarting the backend — clean success.

phase7-004-chat-artifact-open-fix — user reported the Chat assistant's
analysis response looked cut off and asked if there was a token
limit. Confirmed via the real stored summary (2575 chars, complete
sentence, well under the model's real 1536-token ceiling) that this
was NOT a token limit — a hardcoded 300-char preview slice in
backend/app/routes/chat.py. Investigating surfaced a worse bug: the
artifact card's "Open" button was never wired to anything in
ChatPage.tsx (phase7-001). Fixed both: preview trims to a word
boundary, artifact carries deal_id, Open navigates to
/deals/{id}?tab=analysis (new real deep-linking capability added to
DealDetail.tsx). Initial verification was blocked by a real Anthropic
API credit outage; re-ran the full live round-trip once the user
topped up the account — passed cleanly, DoD fully met.

phase7-005-sources-document-list — user asked for the Chat page's
Sources panel to show a deal's related documents when clicked into.
Clicking a Source now selects it as chat context (unchanged) and
expands a real document list underneath (fetchDocuments({deal_id}),
same function used elsewhere in the app) with real download links.
No new backend needed, no LLM call involved — fully verified in a
real browser despite the current Anthropic API credit outage
blocking phase7-004's remaining check.

phase7-006-add-link-source — user asked if Sources could support
adding a link, like NotebookLM. Built a real fetch-and-extract
pipeline (agents/web_source.py: real httpx fetch + real BeautifulSoup
text extraction, not a fabricated summary), with real SSRF protection
(_assert_public_host, tested against 4 real unsafe targets incl. the
AWS/GCP metadata IP, all blocked). documents.source_url column added
for real provenance. build_content_block() gained real .txt support
so link-derived documents are fully analyzable through the existing
pipeline, verified directly bypassing the credit-exhausted Claude
API. Reuses upload_document()'s exact real write path. Full real
browser flow verified: paste URL -> real new document with real page
title, working source link and download link, zero console errors.

phase7-007-auto-summarize-link-source — user asked whether the Agent
can actually read a link source. Traced the real path:
build_deal_context() (what Concierge Q&A reads) only ever surfaces a
document's summary field, and phase7-006 never auto-triggered
summarization, so a freshly-added link sat invisible until someone
separately ran Analyze. Fixed by running a real doc_summarizer call
immediately in create_document_from_url() (just that node, not the
full pipeline). Verified live with real (user-restored) API credits:
a real ~35.8s add-link call produced a real grounded summary,
confirmed via build_deal_context() directly that Concierge's context
now includes it, and a real Concierge Q&A round-trip correctly
referenced the document while honestly declining to state details
beyond its 200-char preview (a pre-existing, deal-context-wide cap
applying to every document type) rather than fabricating an answer.

phase7-008-episodic-chat-memory — user asked for 4 things: real
persistent chat memory, RAG over it, a Knowledge route to summarize
it, and multiple conversation tabs per deal. Confirmed via a
dedicated research pass first that chat had zero DB backing at all
before this. Built chat_conversations/chat_messages (every message
embedded immediately per user's choice), search_chat_history() wired
into concierge_qa for real recall, maybe_digest_conversation() firing
a real Claude synthesis call every 10 new messages into a new
knowledge_base 'chat_insights' category, and a real multi-tab UI in
ChatPage.tsx. Found and fixed 2 real bugs via live testing: Claude's
digest tool_use omitting the required 'topic' field (fallback added),
and real-time per-message embedding hitting Voyage's rate limit
(7/10 failed) — fixed with a batched backfill mirroring documents.py's
existing fix for the same problem. Verified live: a real 5-turn
WebSocket test proved conversation continuity and genuine RAG recall
(a "summarize what we discussed" answer referenced real prior
content), the digest produced a real richly-detailed knowledge_base
row, and a real browser test confirmed tab creation/auto-titling/
switching correctly reloads real persisted history per tab.
