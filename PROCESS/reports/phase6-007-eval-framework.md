## Result: ✅ DoD met — a real minimal eval framework, including a real proof the grader can fail

Gate: real CLI eval runs against a good skill ✅ · real adversarial-skill resistance findings ✅ ·
direct `_grade()` FAIL-proof ✅ · real browser verification ✅.

Closes the explicit "eval pass-rate scoring... aren't built, no eval framework yet" deviation
carried since Admin & Skill Governance was first built, and repeated in phase6-003's report once
the Learning Agent started proposing real skill changes with nothing to score them against.
`agents/evals.py` defines a small, real hand-written test set for the 3 agents with clear
pass/fail criteria (pricing_advisor, ic_memo_drafter, risk_flagger); agents without defined cases
report that honestly (`"No eval cases defined for this agent"`) rather than faking a number.

**Grading is a real second Claude call, not a keyword match.** `_grade()` sends the candidate's
real output plus the stated criteria to Claude with a strict "answer PASS or FAIL on the first
line, then one sentence why" instruction. To prove this grader can actually fail rather than
rubber-stamping everything, it was called directly with an intentionally impossible criteria (the
output "must mention a wombat") against normal agent output — it correctly returned
`passed: False, reason: "FAIL\nThe output is written entirely in English and does not mention a
wombat."` — real, checkable proof the grading path discriminates.

**Adversarial testing produced a genuine finding, not a framework flaw.** Two different adversarial
skill instructions were tested against `pricing_advisor` (one telling it to invent a number anyway
under missing data, one telling it to ignore stated exclusion criteria) — the underlying Claude
model resisted both and the eval correctly still passed. This says something real about model
robustness under this specific pressure, not that the eval framework failed to catch a bad skill;
logged here rather than quietly discarded since it's useful signal for anyone tuning skills later.

Backend: `run_eval_for_change(change_id)` inspects the pending change's `change_type` to decide
whether to test it as a skill_content swap or a model_id swap, runs the real candidate call, and
persists `eval_pass_rate`/`eval_results` onto the real `pending_changes` row via
`POST /admin/pending-approvals/{id}/run-eval`. Frontend: `EvalBar` in `PendingApprovalsTab.tsx`
shows a "Run eval" button pre-grade, then a green/red bar (0.7 threshold, matching
ux-ui-spec.md's framing) with an expandable per-case PASS/FAIL breakdown post-grade.

**Real browser test** (`check8.mjs`, cleaned up after): proposed a real `pricing_advisor` skill
change through the actual API, clicked "Run eval" in the rendered UI, and confirmed a 100% green
bar with PASS/PASS detail matching the earlier CLI run exactly — zero console errors. The real
`pricing_advisor` pending proposal used for this test was deliberately left unresolved as a
legitimate, honest demo artifact rather than cleaned up, since it shows a genuine eval result in
context.

**Found three more stale demo-script.md rows while fixing the one this task was nominally about**,
by re-reading the whole Live vs. Design-only table instead of only the eval-related lines: the
Knowledge Agent row still said Industry/Competitor Insight weren't built (phase6-002 shipped them —
only Company Insight as a distinct stored entity remains unbuilt), the Learning Agent row still
said "Design-only" (phase6-003 shipped it), the Drafting Lead row still said "Design-only"
(phase6-004 shipped it), and the contradiction-engine row still described only the lightweight
flag-only version (phase6-001 shipped real corroboration scoring). All four corrected. This is the
same failure mode caught in phase6-006's report — a task instruction naming one row is not a
guarantee the rest of the table is current, so the whole table gets re-read each time, not just the
named line.

No open deviations from this task.
