Scope: frontend/src/components/dashboard/, frontend/src/pages/Dashboard.tsx, frontend/src/lib/api.ts, backend/app/services/deals.py (add updated_at to response), backend/app/routes/deals.py
Depends on: phase4-000-app-shell-routing (done)
Files allowed to touch: files listed above
DoD:
  - [x] View toggle (Board/Table/Pipeline) in the header row per ux-ui-spec.md Section 3.1
  - [x] Pipeline funnel strip (always visible above the view content) — stage counts, clicking a segment filters Board/Table below
  - [x] Table view: dense rows (Deal name, Client, Industry, Stage Diagram compact, Owner, Docs pending, Status, Last activity)
  - [x] Pipeline view (as a toggle option): full list with per-stage progress bars
  - [x] Right rail "Needs attention" panel — deals Needs attention/Stalled, computed not manually curated
  - [x] New Deal button + modal, POSTs to the real /deals endpoint — verified end to end (created a real deal, appeared immediately in the correct Kanban column and the funnel count updated)
  - [x] Bonus fix: `risk_flags` in the /deals response now reads the real latest risk_flagger output (was hardcoded to 0 in phase1-006 before the Analyst Lead existed)
  - [x] Verified in a real browser: all 3 views render real data correctly, stage-segment filtering works, deal creation persists and appears. Diagnosed an apparent Kanban/rail visual overlap down to root cause (DOM measurements) — confirmed NOT a data-loss bug, just a horizontally-scrollable Kanban with no scroll-affordance UI when 7 columns + a 240px rail don't all fit; logged as a minor polish item, not chased further.
