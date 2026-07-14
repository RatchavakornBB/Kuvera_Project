Scope: frontend/src/pages/ChatPage.tsx
Depends on: phase7-001 (Chat page rebuild), existing fetchDocuments()/documentDownloadUrl() (Phase
2/phase4-002)

Scope: user asked for the Chat page's Sources panel to show each deal's related documents when
clicked into. Reuses the exact same real endpoints the Documents & Contracts screen and Deal
File Library already use — no new backend work needed.

DoD:
  - [x] Clicking a Source (deal) row both selects it as chat context (unchanged prior behavior)
        AND expands to show that deal's real documents (`fetchDocuments({ deal_id })`), fetched
        only when a deal is selected (`enabled: !!selectedDeal`)
  - [x] Each expanded document row shows its real name and a real download link
        (`documentDownloadUrl()`, same backend-mediated download path used everywhere else in the
        app) — download click doesn't also toggle the deal's selection (`stopPropagation`)
  - [x] Empty state ("No documents uploaded for this deal yet") and loading state handled, not
        just the happy path
  - [x] Clicking the same deal again collapses it (deselects), matching existing toggle behavior
  - [x] Verified in a real browser (no Claude API call needed — pure Postgres-backed document
        listing): clicking Deal A correctly expanded to show its real 7 documents with working
        download links, clicking again correctly collapsed back to just the 4 deal rows, zero
        console errors. `tsc --noEmit` clean.
