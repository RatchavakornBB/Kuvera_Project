Scope: supabase/migrations/<new>_create_learning_digests.sql, agents/learning_agent.py,
agents/agent_config.py, agents/adapters/model_adapter.py, backend/app/services/learning.py,
backend/app/routes/learning.py, backend/app/main.py, frontend/src/lib/api.ts,
frontend/src/components/admin/LearningAgentTab.tsx, frontend/src/pages/AdminGovernance.tsx
Depends on: phase5-006 (Admin & Skill Governance / pending_changes queue), phase6-002 (proved the
web_search + custom-tool mixing pattern this reuses)

Scope, per system-architecture.md Section 10.3: "a separate background agent from Knowledge
Agent... continuously ingests the outside world," feeding (1) Industry/Competitor Brief refresh
(already covered by phase6-002 — Learning Agent doesn't duplicate that pipeline) and (2) proposed
Skill additions "subject to the same eval + admin approval gate as any other agent change." Built
(2) as a REAL integration: a proposal is a genuine `pending_changes` row, reviewed in the same real
Pending Approvals tab a human-authored change uses — not a separate, weaker, or fabricated path.
On-demand for now (no scheduler exists yet); should be retrofitted onto phase6-006's real scheduler
once built, same note as phase6-002's Briefs.

DoD:
  - [x] `learning_digests` table + seeded `agent_configs` row for `learning_agent`
  - [x] `agents/agent_config.py::propose_skill_addition()` — appends to (doesn't replace) the
        target agent's current skill_content and files a real `pending_changes` row
  - [x] `agents/learning_agent.py::run_learning_cycle(category, topic)` — real Claude call mixing
        the `web_search` server tool with a custom `report_digest` tool (verified this combination
        actually works in one call, wasn't assumed); the model decides whether to propose a skill
        update, and is instructed most cycles should propose nothing
  - [x] Backend: `POST /admin/learning/run`, `GET /admin/learning/digests`
  - [x] Frontend: new Learning Agent tab in Admin — trigger form + digest history, a badge on any
        digest that filed a real proposal
  - [x] Verified end to end with a real, relevant topic (Thailand PDPA enforcement relevant to
        healthcare M&A): real current regulatory findings (specific 2025 fine amounts, a real new
        June 2026 certification framework) came back, and the model correctly proposed a real,
        well-reasoned addition to risk_flagger's skill_content — confirmed the resulting
        pending_changes row appears in the real Pending Approvals tab, and confirmed in a real
        browser session with zero console errors
