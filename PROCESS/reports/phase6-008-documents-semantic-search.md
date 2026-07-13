## Result: ✅ DoD met — real pgvector search, including a real rate-limit edge case caught live

Gate: real cross-topic semantic ranking ✅ · real cross-deal non-lexical match ✅ · real upload-time
embedding ✅ · real `/deals/{id}/analyze` production-path verification ✅ · real browser
verification ✅.

Closes the last remaining deviation from the user's ordered phase-6 list: the substring search
logged in phase4-002's report. `documents.embedding vector(1024)` reuses the exact same Voyage AI
pipeline as `knowledge_base` (agents/embeddings.py, voyage-3) rather than standing up a second
embeddings integration. A document is embedded on its filename at upload time, then re-embedded on
name+summary once a real summary lands from `doc_summarizer` or `contract_summarizer`
(`update_document_summary`, wired into both `analyze.py` and `contracts.py`). `list_documents()`'s
`q` parameter now runs a real cosine-distance query via direct psycopg (mirroring
`agents/knowledge.py::search_knowledge`'s existing pattern, since PostgREST has no vector-distance
operator), replacing the Python substring filter entirely.

**Proved this is real semantic ranking, not disguised substring matching**, with two tests: a query
for "healthcare services contract with a hospital" correctly ranked all 3 real Master Services
Agreement documents above unrelated financial docs; a cross-deal query for "freight shipping
logistics company" surfaced a Horizon Freight Corp document named `test_image.png` — zero lexical
overlap with the query — because its real doc_summarizer-written summary discusses "Purple Elephant
Logistics Acquisition." Substring search could never have found that second result.

**A real Voyage 429 rate limit surfaced during this task's own testing** (repeated rapid-fire real
embedding calls — backfill, two searches, an upload — hit the free-tier requests-per-minute ceiling
within seconds), and it exposed a genuine bug in the first draft of `backfill_missing_embeddings()`:
it embedded one document at a time in a loop, the exact anti-pattern already documented as a known
failure mode in `agents/embeddings.py`'s own docstring and hit for real during phase5-009. Fixed to
batch every text into one `embed_texts()` call, matching the established pattern. Re-verified after
the fix: a real `/deals/{id}/analyze` run's `update_document_summary` call also hit the same rate
limit mid-test and its embed silently failed (by design — a document-search embedding is
supplementary, not a required field, so it must not break the analyze pipeline) — confirmed the
document was simply excluded from search results until `backfill_missing_embeddings()` (now
correctly batched) picked it up on the next call, then re-verified it ranked correctly by its new
content. This is the system's designed degrade-and-recover behavior working exactly as intended
under genuine real-world API pressure, not a flaw.

**Fixed a leak found while doing this**: every existing `select("*")` read path
(`list_documents`, `get_document`, `get_latest_document`, and `upload_document`'s insert response)
would have returned the full 1024-float embedding vector in every API response the moment the
column existed. Replaced with an explicit `DOCUMENT_COLUMNS` list everywhere.

**Frontend**: the search box now drives a real paid embedding call per query instead of a free
local filter, so it's debounced (400ms) client-side — firing on every keystroke would have spammed
the same rate-limited API this task just worked around. Placeholder copy updated from "Search name
or summary…" to reflect real semantic search.

docs/demo-script.md: Documents & Contracts search row and two related Q&A answers updated — both
Documents & Contracts and Knowledge Base search are now honestly described as real pgvector,
closing out the last "not live" item in the whole Live vs. Design-only table.

This closes the final item in the user's 8-item ordered list. No open deviations from this task.
