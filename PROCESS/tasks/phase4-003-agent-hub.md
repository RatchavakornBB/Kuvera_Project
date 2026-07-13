Scope: agents/activity_log.py, backend/app/services/agent_hub.py, backend/app/routes/agent_hub.py,
backend/app/main.py, frontend/src/lib/api.ts, frontend/src/pages/AgentHub.tsx, frontend/src/App.tsx
Depends on: phase4-002 (done)
Files allowed to touch: files listed above

Explicit scope note (5day-build-timeline.md line 252 + line 23's MVP-vs-Full-Product table):
"Light Agent Hub: a static activity log table (which node ran, when, success/fail) reading from
LangGraph Checkpointer state — not the full live graph view." ux-ui-spec.md Section 3.5 describes a
much larger surface (21-agent grid, sparklines, live graph view, Admin approval links) explicitly
marked as deferred to the Full Product column in the same doc's MVP-vs-Full-Product table. Building
the timeline's scoped-down version, not the full spec section.

DoD:
  - [x] `agents/activity_log.py`: reconstructs a real node-level run trace from the actual
        Postgres Checkpointer `checkpoints` table (thread_id, checkpoint->ts, updated_channels
        mapped to node names via the known AnalystState field ownership, status derived from
        whether pricing_advisor's output carries `pricing_error`)
  - [x] Backend enriches each event with the real deal name / document name (existing Supabase
        client, not new tables)
  - [x] GET /agent-hub/activity returns the trace, most recent first
  - [x] Frontend /agent-hub page: a single real activity log table (timestamp, deal, document,
        node, status) — no fabricated agent grid, no sparklines, no live graph (out of scope per
        the note above)
  - [x] Verified end to end in a real browser: load the page and see the real trace of this
        session's actual /analyze runs on Deal A (both the phase4-001c initial run and the
        regenerate), correct node names and statuses, zero console errors
