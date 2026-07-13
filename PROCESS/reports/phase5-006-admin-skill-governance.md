## Result: ✅ DoD met — the real-scoped governance loop, verified at every layer

Gate: `npx tsc --noEmit` ✅ · real HTTP verification of every backend endpoint ✅ · real browser
end-to-end test (Playwright) ✅ · the one non-negotiable proof — that an approved change actually
changes a real Claude API call, not just UI state — verified twice, at two different layers.

This was previously logged as a design-only candidate (5day-build-timeline.md explicitly lists
"Skill self-creation governance UI" under Design-only). The user asked to build it after the 5-day
plan finished; scope was confirmed via `AskUserQuestion` before starting: a "real-scoped" version
(Agents & Models, Skills, Pending Approvals, Audit Log — all genuinely DB-backed and wired into
`call_model()`), explicitly excluding the Knowledge Base tab and eval pass-rate bar since nothing
in this codebase backs either honestly (no Knowledge Agent, no eval framework exist anywhere).

**Architecture:** new tables `agent_configs` / `pending_changes` / `audit_log`
(migration `20260713130932_create_governance_tables.sql`, applied via `supabase migration up`
without touching existing data). `agents/agent_config.py` reads `agent_configs` by `agent_name`;
`agents/adapters/model_adapter.py`'s `call_model()` — the one chokepoint every node already goes
through, per AGENT.md's own invariant — now looks this up on every real invocation (no caching
across the process lifetime) and uses the DB `model_id` for real provider dispatch and the DB
`skill_content` as a real injected `system` prompt. This means the whole governance loop slots into
existing architecture rather than requiring every node to be touched individually.

**Proof this isn't decorative, done twice:**
1. Set a distinctive skill string directly, called `call_model('doc_summarizer', ...)` at the raw
   Python level, and got back a response literally beginning with the injected marker text —
   confirms the injection mechanism itself.
2. Did the full real workflow through the actual HTTP API: proposed a real skill change for
   `risk_flagger` ("always flag PDPA data-privacy exposure as high-severity"), approved it via
   `POST /admin/pending-approvals/{id}/approve`, confirmed `agent_configs` updated and `audit_log`
   recorded it, then called `call_model('risk_flagger', ...)` with a prompt about undisclosed health
   data — the real Claude response explicitly called out PDPA as a separate high-severity risk,
   unprompted by the test message itself. Left this approved change in place as legitimate real
   governance history (plausible, useful, not embarrassing) rather than reverting it.

**Frontend:** `/admin` route + Sidebar nav item (no RBAC gate — none exists anywhere in this app,
so it's a normal nav item, not actually role-restricted; noted honestly rather than faking a lock
icon). `SkillsTab` uses a real LCS-based line diff (`lib/diff.ts`, no new dependency) against the
agent's current skill_content, not a placeholder. Verified in a real browser: proposed a change on
`ic_memo_drafter` via the Skills tab, watched the diff render correctly (added line highlighted
green), saw it appear in Pending Approvals with the same diff, approved it, watched it disappear
from Pending and appear in the Audit Log with the real timestamp — all against the real backend,
zero console errors.

Deviations from spec (both decided with the user before building, not discovered mid-task):
Knowledge Base tab and eval pass-rate bar omitted entirely rather than built with fabricated data.

Bug found and fixed as a side effect of the audit that led into this task (separate commit,
phase5-007): `POST /deals/{deal_id}/analyze` didn't verify `document_id` belonged to `deal_id` — a
real AGENT.md Section 11 violation, not hypothetical.
