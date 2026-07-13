Scope: supabase/migrations/<new>_add_documents_embedding.sql, backend/app/services/documents.py,
backend/app/services/analyze.py, backend/app/services/contracts.py, backend/app/routes/documents.py,
frontend/src/pages/DocumentsContracts.tsx, docs/demo-script.md
Depends on: agents/embeddings.py (Voyage AI infra built for the Knowledge Agent, phase5-009)

Scope: closes the "substring search, not real pgvector semantic search" deviation logged in
phase4-002's report — the last item in the user's explicit ordered phase-6 list. Adds a real
`embedding vector(1024)` column to `documents`, reusing the exact same Voyage AI pipeline as
`knowledge_base` (no second embeddings integration). A document is embedded on its name at upload
time, then re-embedded on name+summary once a real summary lands (doc_summarizer or
contract_summarizer). `list_documents()`'s `q` parameter now runs a real pgvector cosine query
(direct psycopg connection, mirroring `agents/knowledge.py::search_knowledge`'s pattern) instead of
a Python substring filter.

DoD:
  - [x] `documents.embedding vector(1024)` column + hnsw index added
  - [x] Upload-time embedding (`upload_document`) and re-embed-on-summary
        (`update_document_summary`, wired into both `analyze.py` and `contracts.py`) — both
        best-effort, swallow their own embeddings-provider failures rather than breaking the
        write path
  - [x] `_search_documents()`: real cosine search, same deal_id/type/status filters as before,
        `embedding is not null` excludes rows never successfully embedded
  - [x] `backfill_missing_embeddings()` + `POST /documents/backfill-embeddings` — catch-up for
        pre-migration rows; batches into ONE Voyage call (embed_texts), not one call per doc —
        the per-record version hit a real 429 during this task's own testing, see Errors below
  - [x] Every read path (`list_documents`, `get_document`, `get_latest_document`,
        `upload_document`'s insert response) uses an explicit column list excluding `embedding` —
        a 1024-float vector has no business in an API response
  - [x] Frontend: search input debounced (400ms) — it now drives a real paid embedding call per
        query, not a free local filter; placeholder copy updated to reflect real semantic search
  - [x] docs/demo-script.md: Documents & Contracts search row + two related Q&A answers updated
  - [x] Verified past "no error thrown": (1) real backend query for "healthcare services contract
        with a hospital" correctly ranked all 3 real MSA/contract documents above unrelated
        financial docs; (2) a cross-deal query for "freight shipping logistics company" correctly
        surfaced a Horizon Freight Corp document whose filename ("test_image.png") has zero lexical
        overlap with the query — matched purely on its real summary text ("Purple Elephant
        Logistics Acquisition"), proving this isn't disguised substring matching; (3) uploaded a
        real test document and confirmed it was immediately semantically searchable via its
        filename-only embedding, then cleaned it up; (4) triggered a real `/deals/{id}/analyze` run
        and confirmed `update_document_summary`'s re-embed path executes without error against the
        production code path, not just a direct unit call; (5) real browser test — typed a query
        into the actual rendered search box and confirmed the same ranking as the CLI test,
        zero console errors
