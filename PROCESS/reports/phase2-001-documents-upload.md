## Result: ✅ DoD met

Gate: manual verification only (no automated test suite for routes yet) — `supabase db reset` created the `deal-documents` private bucket cleanly; `curl -F file=@...` uploaded a real generated test PDF (`backend/tests/fixtures/deal_a_financial_summary.pdf`, a synthetic-but-realistic Deal A financial summary written for this and the upcoming node tests) to Deal A; downloaded the object back via `supabase-py` and confirmed real PDF bytes (`%PDF` magic number), confirmed the matching `documents` row exists with `storage_path` set.

Deviations from spec: none. Compensating cleanup (delete the storage object if the DB insert fails) is implemented but not yet exercised by an actual failure — noted as a risk, not a gap, since forcing that failure path isn't worth a dedicated test at this stage.

Risks: none new. The uploaded test document is being kept (not deleted) so the next task (3.1 doc_summarizer) can run against a real already-uploaded document instead of re-uploading.
