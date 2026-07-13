Scope: supabase/migrations/<new>_create_agent_invocations.sql, agents/activity_tracker.py,
agents/adapters/model_adapter.py, backend/app/services/agent_hub.py,
backend/app/routes/agent_hub.py, frontend/src/lib/api.ts,
frontend/src/components/agentHub/AgentGrid.tsx, AgentDetailPanel.tsx, LiveGraphView.tsx,
frontend/src/pages/AgentHub.tsx
Depends on: every real agent built through phase6-004 (Contradiction engine, Knowledge Agent,
Learning Agent, Drafting Lead) — this task is what makes all of them operationally visible, not
just individually functional.

Scope, per ux-ui-spec.md Section 3.5 vs. reality: the spec frames this as "all 21 agents." This
codebase has 13 real agents (agent_configs rows) — doc_summarizer, risk_flagger, ic_memo_drafter,
pricing_advisor, contract_summarizer, clause_extractor, concierge_qa, orchestrator,
knowledge_promoter, industry_brief, competitor_brief, learning_agent, drafting_lead. The grid shows
these 13, honestly labeled as what's actually implemented — not padded to 21 with agents that
don't exist (Knowledge/Learning Agent's own sub-functions count as their real, distinct agents
here, which is a defensible reading, but there's no invented filler).

Real infrastructure gap found and fixed first: before this task, only the 4 Analyst Lead nodes had
any activity trail (reconstructed from LangGraph's checkpointer, phase4-003) — the other 9 real
agents had no status signal at all. Instrumented `call_model()` itself (the one chokepoint every
agent already goes through) to log a real `agent_invocations` row on every call — 'running' at
start, 'success'/'error' at completion — giving every agent uniform, real status tracking.

DoD:
  - [x] `agent_invocations` table; `call_model()` logs every real invocation (best-effort —
        logging failures never break the real LLM call)
  - [x] Backend: `GET /agent-hub/grid` (real status per agent, grouped by Lead), `GET
        /agent-hub/agents/{name}` (real recent invocations + real 7-day sparkline, not backfilled/
        fabricated history), `GET /agent-hub/graph/analyst-lead` (mirrors agents/graph.py's actual
        edges, real per-node status)
  - [x] Frontend: `AgentHub` now has 3 views — Agent Grid (new, default; status/provider filter
        bar), Live Graph (new; real SVG of the Analyst Lead's actual structure, polls every 3s,
        the currently-running node highlights), Activity Log (existing phase4-003 log, kept
        unchanged and still working)
  - [x] Agent detail click-through: real sparkline + real recent-invocation history
  - [x] Verified end to end: triggered real calls across multiple agents (doc_summarizer,
        concierge_qa), confirmed the grid showed correct real "Xm ago" / "just now" timestamps and
        the right agent grouped under the right Lead; opened a detail panel and confirmed its
        sparkline/history matched; switched to Live Graph and confirmed it renders the real
        gate+fan-out shape; confirmed the existing Activity Log view still works unchanged; found
        and fixed a real SVG coordinate bug (a node's right edge exceeded the declared viewBox
        width, clipping it) via a fresh screenshot after the fix; zero console errors throughout
