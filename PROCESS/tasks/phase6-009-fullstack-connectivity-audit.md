Scope: frontend/src/lib/api.ts, frontend/src/components/documents/UploadDocumentModal.tsx,
agents/nodes/clause_extractor.py
Depends on: nothing new — an audit pass over everything shipped through phase6-008

Scope: user asked (2026-07-13, in Thai, mid-task) to verify frontend and backend features are
complete and fully connected before considering the phase-6 extension finished. Not new feature
work — a systematic cross-reference of every backend route against every frontend caller, and vice
versa, followed by fixing whatever real gaps that surfaced (matching this session's established
pattern: audits that find real bugs close them, not just report them).

Method: enumerated every `@router.*`/`@library_router.*` decorator across backend/app/routes/*.py
against main.py's registered prefixes, then grepped every `${API_BASE_URL}/...` fetch call in
frontend/src/lib/api.ts, then verified every exported api.ts function actually has a caller
somewhere in frontend/src (not just defined-and-unused).

DoD:
  - [x] Full route inventory cross-referenced both directions (backend -> frontend caller exists;
        frontend api.ts export -> has a real component caller) — every api.ts export has at least
        one real caller, no orphaned wrappers
  - [x] Two real, intentional non-connections identified and confirmed NOT bugs:
        `POST /deals/{id}/ask` (concierge Q&A) is deliberately superseded by the `/chat` WebSocket,
        which calls `concierge_service.ask_about_deal` in-process — documented in the route's own
        docstring, not an oversight; `POST /documents/backfill-embeddings` is a deliberate
        maintenance-only endpoint (phase6-008), not meant for end-user UI
  - [x] One real, unintentional gap found and fixed: `POST /contracts` (4.1 contract_summarizer +
        4.2 clause_extractor — the actual "Contracts" half of "Documents & Contracts") had ZERO
        frontend caller anywhere. The only Contract-type document in the system was hand-seeded in
        supabase/seed.sql, not produced by a real user action — this pipeline had never been
        exercised through the live app since Phase 3. Fixed: added `uploadContract()` to api.ts and
        a "This is a contract (run clause extraction)" checkbox to UploadDocumentModal.tsx, wired
        to the real, pre-existing, working backend endpoint
  - [x] Wiring up that dead code path immediately surfaced a real, previously-latent bug: the very
        first live end-to-end contract upload stored `documents.clauses` as a 2163-character JSON
        *string* (a redundant stringified `{"clauses": [...]}` wrapper) instead of a real array —
        `clause_extractor.py` had no defense against Claude occasionally returning a JSON-encoded
        string for an array-typed tool_use field, the same failure mode `agents/knowledge.py`'s
        `_normalize_field` already defends against for object-typed fields, just never applied
        here. Confirmed this was a genuine live-pipeline bug, not old corrupted data, by checking
        the pre-existing seed Contract document's `clauses` column — a clean real Python list,
        because it was inserted directly by seed.sql, never through the (until now, unreachable)
        live pipeline
  - [x] Fixed with a `_normalize_clauses()` helper (parses the string, unwraps the redundant
        `clauses` key if present, falls back to `[]` if genuinely unparseable) mirroring
        `agents/knowledge.py`'s established pattern
  - [x] Verified past "no error thrown": ran the exact same real contract upload twice — once
        before the fix (reproduced the corruption for real, then cleaned up the corrupted test row)
        and once after (real Claude call returned a clean 8-item array, verified directly against
        the DB column type and a rendered browser screenshot showing the document listed with type
        "Contract"), zero console errors both times
