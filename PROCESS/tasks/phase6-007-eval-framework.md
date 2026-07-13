Scope: supabase/migrations/<new>_add_eval_columns.sql, agents/evals.py,
backend/app/services/governance.py, backend/app/routes/governance.py, frontend/src/lib/api.ts,
frontend/src/components/admin/PendingApprovalsTab.tsx, frontend/src/pages/AdminGovernance.tsx,
docs/demo-script.md
Depends on: existing Pending Approvals / governance queue (Phase 3), Learning Agent's skill
proposals (phase6-003)

Scope: closes the "eval pass-rate scoring from the design doc isn't built, no eval framework yet"
deviation logged during Admin & Skill Governance and repeated in phase6-003's report. Builds a
minimal, real eval framework: a small set of hand-written test cases per agent (prompt + pass/fail
criteria), a real candidate call against the proposed skill/model, and a real second Claude API
call acting as an LLM-as-judge to grade PASS/FAIL with a reason. Results are stored on the
`pending_changes` row and surfaced as a real on-demand pass-rate bar in the Pending Approvals UI —
run manually per proposal, not on a background schedule, since it's a real paid Claude call.

DoD:
  - [x] `pending_changes.eval_pass_rate` (real) and `eval_results` (jsonb) columns added
  - [x] `agents/evals.py`: real eval cases defined for 3 agents (pricing_advisor, ic_memo_drafter,
        risk_flagger — the ones with clear, checkable pass/fail criteria); agents without defined
        cases return `{"pass_rate": None, "note": "No eval cases defined for this agent"}` rather
        than a fabricated score
  - [x] Real LLM-as-judge grading (`_grade()`): a second real Claude call graded strictly on stated
        criteria, forced to answer PASS/FAIL on the first line
  - [x] `run_eval_for_change()`: determines whether the proposed change is a skill_content or
        model_id swap and runs the candidate accordingly, stores results back onto the real
        `pending_changes` row
  - [x] `POST /admin/pending-approvals/{change_id}/run-eval`
  - [x] Frontend: `EvalBar` in `PendingApprovalsTab.tsx` — "Run eval" button when ungraded, a real
        green/red bar (0.7 pass-rate threshold) with an expandable per-case PASS/FAIL detail list
        once graded
  - [x] docs/demo-script.md updated: Admin & Skill Governance row, plus stale Q&A text and three
        other stale Live-vs-Design-only rows found while re-reading the whole table (Knowledge
        Agent's Industry/Competitor Insight, Learning Agent, Drafting Lead, contradiction engine —
        all previously marked not-built/design-only, all actually shipped in phase6-001..004)
  - [x] Verified past "no error thrown": (1) real CLI run with a genuinely good pricing_advisor
        skill scored 100%; (2) two different adversarial skill instructions (attempting to make the
        agent invent numbers / ignore missing data) were both correctly resisted by the underlying
        model and still passed real grading — a real finding about model robustness, not a
        framework bug; (3) `_grade()` called directly with an intentionally unsatisfiable criteria
        ("must mention a wombat") produced a real, correct FAIL with a real reason string; (4) real
        browser test: proposed a real `pricing_advisor` skill change via the API, clicked "Run
        eval" in the actual rendered UI, confirmed the green 100% bar and PASS/PASS detail matched
        the CLI result exactly, zero console errors
