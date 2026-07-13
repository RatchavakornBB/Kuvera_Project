Scope: backend/app/routes/documents.py, backend/app/services/documents.py,
backend/app/main.py, frontend/src/lib/api.ts, frontend/src/App.tsx,
frontend/src/pages/DocumentsContracts.tsx,
frontend/src/components/documents/DocumentTable.tsx,
frontend/src/components/documents/DocumentDetailPanel.tsx,
frontend/src/components/documents/UploadDocumentModal.tsx,
frontend/src/components/documents/KeyDatesStrip.tsx
Depends on: phase4-001d (done) — reuses uploadDocument() from lib/api.ts
Files allowed to touch: files listed above
DoD:
  - [x] New GET /documents (cross-deal) with deal_id/type/status/q filters, joined with the
        owning deal's name — backs the whole screen (ux-ui-spec.md Section 3.4)
  - [x] Document list table: name, deal (linking to Deal Detail), type, uploaded date, one-line
        AI summary, approval status chip, key date with a countdown badge when within 30 days
  - [x] Search bar filters by name/summary (substring match, not real pgvector semantic search —
        see deviation note below) + filter-by-deal / type / status
  - [x] Upload button opens a modal to pick a deal + file, reuses the existing real
        POST /deals/{id}/documents path (no new upload code, no duplicate write path)
  - [x] Document detail side panel on row click: full summary, extracted clauses (4.2) as a
        labeled list, status, link to the owning deal
  - [x] Key-dates strip: banner listing documents with key_date within 30 days
  - [x] Verified end to end in a real browser: load the screen with real cross-deal data,
        search/filter, open a document's detail panel, upload a real file via the modal and see
        it appear in the list, zero console errors

Known deviation (log before building, not after): ux-ui-spec.md calls for "semantic search via
pgvector," but no embeddings pipeline exists anywhere in this codebase yet (system-architecture.md
Section 9/10 describes pgvector as a *scaling-phase* addition, not built for the MVP). Implementing
substring search on name/summary now; true semantic search is out of scope for this task.
