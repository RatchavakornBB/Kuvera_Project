## Result: ✅ DoD met

Gate: `npx tsc --noEmit` ✅ · real browser end-to-end test (Playwright) ✅.

Built per the timeline's explicit scoped-down instruction (5day-build-timeline.md line 252): a
static activity log, not the full ux-ui-spec.md Section 3.5 surface (21-agent grid, sparklines,
live graph) — that fuller vision is the doc's own "Full Product" column, not MVP.

`agents/activity_log.py` reads the real LangGraph Postgres Checkpointer `checkpoints` table
directly (the same one `agents/graph.py`'s `PostgresSaver` already writes to on every `/analyze`
run) and reconstructs node-level events: each checkpoint's `updated_channels` field names are
mapped back to the node that owns writing them (`summary` → doc_summarizer, `risk_flags` →
risk_flagger, `ic_memo_draft` → ic_memo_drafter, `pricing_note` → pricing_advisor), using the
checkpoint's own `ts` for real timestamps. `backend/app/services/agent_hub.py` enriches each event
with the real deal/document name via the existing Supabase client. New `GET /agent-hub/activity`
and the `/agent-hub` frontend page render the trace as a single table.

Bug found and fixed before considering this done: the Analyst Lead's fan-out step (ic_memo_drafter
and pricing_advisor run in parallel via `Send()`, agents/graph.py) writes both nodes' output into
the *same* checkpoint row. My first pass used `next()` to find the first matching channel, which
silently dropped pricing_advisor from the log every time it ran alongside ic_memo_drafter. Caught
this by inspecting real query output before writing the frontend (not by chance) — fixed by
emitting one event per matched node instead of stopping at the first match, then re-verified via
curl that both nodes now appear for every fan-out step.

Verified end to end: loaded `/agent-hub` in a real browser and saw the actual trace of every
`/analyze` run made during this session (phase4-001c's initial run and regenerate, both on Deal A's
`deal_a_customer_msa.pdf`), correct node labels, correct real timestamps, "success" status on every
row (no failures occurred in this session to exercise the "failed" — red — path, but the status
logic itself is exercised by real `pricing_error` presence/absence, not a hardcoded value). Clicking
a deal link navigated to the real Deal Detail page. Zero console errors.

Deviations from spec: the 21-agent grid, sparklines, live LangGraph-structure view, and Admin
approval-queue links from ux-ui-spec.md Section 3.5 are not built — explicitly out of scope per the
timeline's MVP-vs-Full-Product table (5day-build-timeline.md line 23).
