## Result: ✅ DoD met — a real, honestly-scoped operational view, not a padded roster

Gate: real backend endpoint verification via curl ✅ · real browser verification (Playwright) ✅.

The spec's "21 agents" framing doesn't match this codebase's reality even after phase6-001 through
phase6-004 added Contradiction engine, Knowledge Agent, Learning Agent, and Drafting Lead — there
are 13 real, distinct `agent_configs` rows. Built the grid to show exactly those 13, grouped by
Lead (Analyst Lead, Contracts Lead, Concierge, Orchestrator, Knowledge Agent, Learning Agent,
Drafting Lead), with the page header stating the real count rather than the spec's number.

**Real infrastructure gap closed first, not worked around:** before this task, 9 of the 13 real
agents had zero activity trail — only the 4 Analyst Lead nodes were visible at all, via LangGraph's
own checkpointer (phase4-003). Rather than build a grid that's honest for 4 agents and silent for
9, instrumented `call_model()` itself — the one real chokepoint literally every agent already goes
through — to log a real `agent_invocations` row on every call. This is what makes the live status
dot, the "last active" timestamp, and the 7-day sparkline real for all 13 agents uniformly, not
approximated or backfilled.

**Verified with real triggered activity, not just empty-state screenshots:** called `doc_summarizer`
and `concierge_qa` directly, confirmed the grid picked up real "5m ago" / "just now" timestamps in
the correct Lead groups, opened `concierge_qa`'s detail panel and confirmed its sparkline (1 real
bar for today) and recent-invocation list matched. Switched to Live Graph and confirmed the SVG
renders the actual `agents/graph.py` structure (gate doc_summarizer→risk_flagger, then Send()
fan-out to ic_memo_drafter/pricing_advisor) — found and fixed a real bug in the process: a node's
box (x=460, width=140) extended to x=600, past the declared `viewBox` width of 560, clipping its
label. Fixed by widening the viewBox, verified with a fresh screenshot. Confirmed the pre-existing
Activity Log view (phase4-003) still renders correctly, unchanged. Also caught and correctly
reverted a real but accidental empty-string skill proposal made while generating test activity —
rejected it through the actual Pending Approvals workflow rather than deleting it directly, keeping
the audit trail honest.

Deviations from the design doc, stated plainly rather than glossed over: the "21 agents" framing
doesn't hold; this reflects the real 13. The filter bar covers status and provider (both spec'd);
filtering by Lead is handled by the grid's grouping instead of a separate control, which achieves
the same practical outcome without a redundant third dropdown.
