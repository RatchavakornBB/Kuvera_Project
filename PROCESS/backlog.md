# PROCESS/backlog.md — ready / blocked / deferred work

## Ready
- [ ] phase1-007-table-pipeline-view — Table view + Pipeline funnel strip + filter bar + New Deal button (ux-ui-spec.md Section 3.1), deferred out of phase1-006 which only wired the already-built Board/Kanban view.
- [ ] phase3-001-contracts-lead — /contracts endpoint, 4.1 summarizer + 4.2 clause extractor nodes (timeline Section 6 Phase 3, 09:00–10:30).
- [ ] phase3-002-concierge-qa — RAG over seeded deal data with deal_id-scoped filter on "Ask about this deal" panel (timeline Section 6 Phase 3, 10:30–12:00). This is one of the non-negotiable invariants (AGENT.md Section 11) — never blend data across deals.
- [ ] phase3-003-chat-panel — convert Chat panel components from the mockup (message thread, composer, inline artifact card).
- [ ] phase3-004-chat-websocket — wire Chat panel to /chat WebSocket, Orchestrator routing between Concierge Q&A and Analyst subgraph.
- [ ] phase3-005-web-search-edgar — web_search/web_fetch + SEC EDGAR tool wiring on the Analyst Lead.
- [ ] phase4-001-deal-detail — convert Deal Detail shell + Overview/Documents/Analysis tabs, wire to real /deals/{id} and /analyze data.
- [ ] phase4-002-agent-hub — static activity log table reading from the LangGraph Checkpointer's checkpoints table (real data now exists to read from, from Phase 2 testing).

## Blocked
- (none)

## Deferred (found mid-task, not in that task's scope)
- (none)

## Done (Phase 1 + Phase 2, for reference — see PROCESS/reports/ for full detail)
Phase 1 (Foundations): environment setup, 8-table schema, seed data, design tokens,
StageDiagram, DealCard/Kanban, Dashboard wired to real /deals data.

Phase 2 (Core AI Loop): /deals CRUD, document upload -> Storage, call_model() adapter,
3.1 doc_summarizer, 3.2 risk_flagger + contradiction check, 3.3 ic_memo_drafter,
3.4 pricing_advisor, compiled LangGraph (gate + Send() fan-out) with Postgres
Checkpointer, /deals/{id}/analyze wired end to end and verified over real HTTP
(happy path + node-failure path). The core "upload -> AI analysis -> answer" loop
(AGENT.md's never-cut invariant, Section 11/12) now actually works.
