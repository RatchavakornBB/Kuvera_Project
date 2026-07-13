Scope: frontend/src/pages/DealDetail.tsx, frontend/src/components/dealDetail/, frontend/src/App.tsx (route)
Depends on: phase4-000-app-shell-routing (done)
Files allowed to touch: files listed above
DoD:
  - [x] /deals/:id route added, fetches real GET /deals/{id} data (nested contacts/documents/tasks/notes/dd_items/milestones already returned by the backend)
  - [x] Header: deal name, client, industry tags, full StageDiagram, owner — per ux-ui-spec.md Section 3.2
  - [x] Tab navigation: Overview, Documents, Analysis, Tasks & Notes (Industries/Company tabs explicitly skipped — need Knowledge Agent infrastructure that's design-only per system-architecture.md's MVP scope table, not a cut corner)
  - [x] Overview tab: milestone timeline (real dates, done/pending states), contacts (POC), key dates (correctly shows empty state — no documents have a key_date set yet, accurate not broken)
  - [x] "Ask about this deal" side panel wired to the real ShellContext.askAboutDeal, opening the chat panel scoped to this deal — verified the "Scoped to Deal A" chip appears in the real chat panel
  - [x] Clicking a deal from the Dashboard (any of Board/Table) navigates here and shows real data
  - [x] Verified in a real browser against Deal A's real data, zero console errors
