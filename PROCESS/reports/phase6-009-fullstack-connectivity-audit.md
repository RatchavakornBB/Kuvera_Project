## Result: ✅ Audit complete — one real dead code path found and reconnected, one real latent bug found and fixed by exercising it for the first time

Gate: full route inventory cross-referenced both directions ✅ · real live contract-upload
reproduction of the bug before fixing ✅ · real re-verification after fixing ✅ · real browser
verification ✅.

User asked mid-task, in Thai, to verify frontend and backend are complete and fully connected
before treating the phase-6 extension as finished. Enumerated every backend route decorator and
cross-referenced it against every `${API_BASE_URL}/...` call in frontend/src/lib/api.ts, in both
directions.

**Result: every api.ts export has a real caller** — no dead frontend wrappers. Two backend routes
have no frontend caller, and both are legitimate by design, not bugs: `POST /deals/{id}/ask` is
deliberately superseded by the `/chat` WebSocket (which calls the same underlying service
in-process — documented in the route's own docstring, predates this session); `POST
/documents/backfill-embeddings` (phase6-008) is a deliberate maintenance-only endpoint, not
end-user surface.

**One real gap found: `POST /contracts` had zero frontend caller.** This is the actual "Contracts"
half of the "Documents & Contracts" screen — 4.1 contract_summarizer + 4.2 clause_extractor. The
only Contract-type document anywhere in the system was hand-inserted by `supabase/seed.sql`; the
real pipeline had never been exercised through the live app since it was built in Phase 3. Fixed by
adding `uploadContract()` to api.ts and a "This is a contract (run clause extraction)" checkbox to
`UploadDocumentModal.tsx`, wired to the pre-existing, correctly-implemented backend endpoint.

**Wiring that up immediately caught a real, previously-latent bug.** The first live end-to-end
contract upload stored `documents.clauses` as a 2163-character JSON *string* — a redundant
stringified `{"clauses": [...]}` wrapper — instead of a real array. `clause_extractor.py`'s
`_run_once` returned `block.input["clauses"]` unchecked, with no defense against Claude occasionally
returning a JSON-encoded string for an array-typed tool_use field instead of the raw array. This is
the exact failure mode `agents/knowledge.py`'s `_normalize_field` already defends against for
object-typed fields (documented there from real testing) — it was simply never applied to
`clause_extractor`, because nothing had ever called it live to find out.

Confirmed this wasn't old corrupted data by checking the seed Contract document's `clauses` column
directly: a clean real Python list, because seed.sql wrote it directly, bypassing the (until this
task, unreachable) live pipeline entirely. This proves the bug is real and would have hit any
actual user the moment this feature was ever used.

Fixed with `_normalize_clauses()`: parses the string if needed, unwraps the redundant `clauses` key
if the model nested it, falls back to `[]` if genuinely unparseable — mirroring the established
`agents/knowledge.py` pattern rather than inventing a new one.

**Verified by reproducing the bug live, then re-verifying the fix live** — not just reasoning about
the code: re-ran the identical real contract upload (same source PDF, same deal) after the fix and
confirmed via direct DB inspection that `clauses` is now a real Python list (type-checked, not just
"didn't crash"), 8 correctly-shaped `{label, text}` items, and a real browser screenshot showing the
document listed with type "Contract." Both the corrupted test row and the clean re-test row were
cleaned up afterward as unambiguously self-created test artifacts (created and identified within
this same task).

This closes the mid-task audit request. Phase 6 (post-5-day-plan extension) is complete, including
this connectivity pass.
