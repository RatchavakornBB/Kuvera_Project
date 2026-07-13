## Result: ✅ DoD met

Gate: `npx tsc --noEmit` ✅ · real browser end-to-end test (Playwright, against the real backend
and Supabase) ✅.

New backend surface: `GET /documents` (`library_router` in `app/routes/documents.py`,
`list_documents()` in `app/services/documents.py`) — cross-deal, joined with `deal:deals(id,name)`,
filterable by `deal_id`/`type`/`status`/`q`. `q` filters in Python over the fetched rows rather than
building a PostgREST `.or_()` ilike filter, so an arbitrary user search string is never interpolated
into a filter expression.

Frontend: `DocumentsContracts.tsx` (new `/documents` route in `App.tsx`) with a search bar + three
filter dropdowns, a `DocumentTable` (name/deal/type/uploaded/summary/status/key-date with a
countdown badge inside 30 days), a `DocumentDetailPanel` side panel (summary, extracted clauses,
status, link to the owning deal), an `UploadDocumentModal` that reuses the existing real
`uploadDocument()` call (no new/duplicate write path), and a `KeyDatesStrip` banner.

Verified against real cross-deal data (3 documents across Deal A, one a real Contract-type doc with
real extracted clauses from Phase 3 testing): the table rendered all 3 rows correctly; searching
"medico" correctly narrowed to the 2 rows whose real AI summary mentions Siam Medico Holdings and
hid the unrelated financial-statements row; opening the Contract-type row's detail panel rendered
its real extracted clauses (`Term & Renewal`, etc.); opening a row with no clauses correctly showed
"No clauses extracted for this document." (not an error); uploading a real fixture PDF via the
modal took the row count from 3 to 4 and the new file appeared immediately. Zero console errors
throughout.

Deviations from spec (logged before building, per the task file):
1. ux-ui-spec.md calls for "semantic search via pgvector." No embeddings pipeline exists anywhere
   in this codebase — system-architecture.md describes pgvector as a scaling-phase addition, not
   part of the MVP build. Implemented substring search over name/summary instead.
2. "Approval status with change history" (spec's document detail panel) — no audit-log table
   exists for status transitions, so the panel shows current status only, no history. Building a
   full audit trail wasn't in phase4-002's scope and there's no other consumer of that data yet.

Risks: two test-script bugs found during verification (not app bugs) — `page.selectOption('select', ...)`
initially matched the *page's* deal-filter dropdown instead of the upload modal's own select,
because the modal renders on top of a page that already has multiple `<select>` elements; fixed by
scoping the locator to the modal's root (`.fixed.inset-0 select`). Same root cause class as the
`text=Documents` ambiguity hit in phase4-001b — worth remembering that this app reuses select/label
text across overlapping UI layers.
