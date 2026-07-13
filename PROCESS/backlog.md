# PROCESS/backlog.md — ready / blocked / deferred work

## Ready
- [ ] phase4-001d-tasks-notes-tab — Deal Detail Tasks & Notes tab, real tasks/meeting_notes data.
- [ ] phase4-002-documents-contracts-screen — the dedicated Documents & Contracts screen (search, filter, document detail side panel) — separate from the per-deal Documents tab.
- [ ] phase4-003-agent-hub — static activity log table. Real data to read now exists: LangGraph's `checkpoints`/`checkpoint_writes` tables (Postgres Checkpointer, live since Phase 2) actually recorded every node run across all the Phase 2/3 testing.
- [ ] phase4-004-key-date-notifier — 4.3 Key-date notifier (system-architecture.md Section 8), deferred out of phase3-001 since it's explicitly a "scheduled background check," different infrastructure than the ingest-triggered 4.1/4.2.
- [ ] phase5-admin-skill-governance — Admin & Skill Governance screen (design-only candidate — check with user whether this stays design-only per the MVP scope table before building).

## Blocked
- (none)

## Deferred (found mid-task, not in that task's scope)
- (none)

## Minor polish (accepted, not a functional bug)
- Kanban board: 7 columns + the 240px Needs Attention rail don't all fit at once at typical
  viewport widths. Proven via real DOM measurement (`getBoundingClientRect`/`scrollWidth`/
  `clientWidth`) that the board is correctly bounded and the hidden column (Nova Fintech) is
  fully reachable by scroll — not a data/overlap bug, just missing a scroll-affordance visual
  hint (fade/shadow). `min-w-0` (AppShell) and `w-full` (KanbanBoard) fixes kept since they're
  correct regardless, but they were not the actual explanation for the tight appearance.

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
section, new GET /deals/{id}/analysis endpoint to hydrate without a fresh LLM run).
