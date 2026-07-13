Scope: supabase/migrations/<new>_create_governance_tables.sql, agents/agent_config.py,
agents/adapters/model_adapter.py, backend/app/services/governance.py,
backend/app/routes/governance.py, backend/app/main.py, frontend/src/lib/api.ts,
frontend/src/pages/AdminGovernance.tsx, frontend/src/components/admin/*.tsx,
frontend/src/App.tsx, frontend/src/components/layout/Sidebar.tsx
Depends on: Phase 5 complete (done). User explicitly asked to build this after it was previously
logged as a design-only candidate (5day-build-timeline.md lists "Skill self-creation governance
UI" under Design-only) — this is a deliberate scope extension past the original 5-day plan, not
scope creep found mid-task.

Scope decision (confirmed with user via AskUserQuestion before starting): build a "real-scoped"
version, not the full ux-ui-spec.md Section 3.6. Concretely:
  - BUILD real: Agents & Models tab (editable model_id, actually changes which model the next real
    call_model() invocation uses), Skills tab (editable skill_content, actually injected into the
    next real LLM call's system prompt), Pending Approvals (real edit -> pending -> approve/reject
    workflow, backed by a real table), Audit Log (real history of approved/rejected changes)
  - SKIP: Knowledge Base tab (no Knowledge Agent exists anywhere in this codebase — nothing real to
    browse), eval pass-rate bar (no eval framework exists anywhere in this codebase — would be a
    fabricated number)
  - The governance loop must wire into the actual `call_model()` chokepoint (agents/adapters/
    model_adapter.py) — AGENT.md's invariant that this is the only LLM access path — not a
    decorative UI that doesn't affect real agent behavior.

DoD:
  - [x] Migration: `agent_configs` (agent_name unique, model_id, skill_content, updated_at),
        `pending_changes` (agent_name, change_type, old_value, new_value, status, timestamps),
        `audit_log` (agent_name, change_type, old_value, new_value, action, created_at) — seeded
        with one `agent_configs` row per agent currently in AGENT_MODELS, empty skill_content
  - [x] `call_model()` looks up the agent's real DB-stored model_id/skill_content on every
        invocation (not cached across the process lifetime) and actually uses them — model_id
        picks the real provider/model, skill_content is injected as the real `system` prompt
  - [x] Backend: GET /admin/agents, POST /admin/agents/{name}/propose, GET
        /admin/pending-approvals, POST /admin/pending-approvals/{id}/approve|reject, GET
        /admin/audit-log
  - [x] Frontend /admin route + Sidebar nav item: Agents & Models tab, Skills tab (editor + diff
        against current value, no fake "live markdown preview" claim — plain text diff), Pending
        Approvals tab, Audit Log tab
  - [x] Verified end to end in a real browser AND against real agent behavior: propose a
        skill_content change for one agent, approve it, then trigger a real node call for that
        agent and confirm (via the raw Anthropic request, not just UI state) the new skill text
        was actually sent as the system prompt — this is the one non-negotiable proof this isn't
        decorative
