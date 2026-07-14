Scope: supabase/migrations/<new>_add_document_source_url.sql, agents/web_source.py (new),
agents/documents.py, backend/requirements.txt, backend/app/services/documents.py,
backend/app/routes/documents.py, frontend/src/lib/api.ts, frontend/src/pages/ChatPage.tsx,
frontend/src/pages/DocumentsContracts.tsx
Depends on: phase7-005 (Sources document list), agents/embeddings.py (Voyage AI, reused for
upload-time embedding)

Scope: user asked whether Sources could support adding a link, like NotebookLM. NotebookLM lets
users add a URL as a source; this app's document model is deal-scoped (every document belongs to
exactly one deal), so the natural, consistent placement — matching phase7-005's newly-added
per-deal document list — is: within a selected deal's expanded Sources view, add a URL and it
becomes a real document for that deal, fetched and stored server-side.

DoD:
  - [x] `documents.source_url text` column added (NULL for ordinary uploads, set only for
        link-derived documents) — real provenance tracking, not stuffed into unstructured text
  - [x] `agents/web_source.py`: real server-side URL fetch (httpx) + real readable-text extraction
        (BeautifulSoup, strips script/style, keeps visible text) — the page's own real content, not
        a fabricated/AI-generated summary
  - [x] Real SSRF protection (`beautifulsoup4` added as a new dependency, `_assert_public_host()`
        resolves the hostname and rejects private/loopback/link-local/reserved/multicast addresses
        before connecting, and re-checks after redirects) — this endpoint fetches arbitrary
        user-supplied URLs server-side, a well-known vulnerability class if left unguarded.
        Documented as a best-effort mitigation (doesn't validate every intermediate redirect hop),
        appropriate for a single-user local app, not claimed as exhaustive
  - [x] Real content caps: 5MB max response size, 15s request timeout, rejects non-HTML/text
        content-types (so someone can't point this at a binary file and get garbage)
  - [x] `agents/documents.py::build_content_block()` gained real `.txt` support (decode as UTF-8,
        wrap as a `text` block) — link-derived documents are fully analyzable through the existing
        doc_summarizer/risk_flagger/etc. pipeline, not a lesser citation-only stub
  - [x] `backend/app/services/documents.py::create_document_from_url()` reuses the exact same real
        write path as a file upload (`upload_document()`, extended with an optional `source_url`
        param) — Storage + DB row together, same embed-on-upload behavior, same invariant
  - [x] `POST /deals/{deal_id}/documents/from-url` — real 400 on an unsafe URL, real 422 with the
        actual fetch error on failure (bad host, non-HTML, oversized, timeout), not a generic 500
  - [x] Frontend: `+ Add link` input inside a selected deal's expanded Sources section (built in
        phase7-005); link-sourced documents show a 🔗 marker and their name links out to the real
        source URL in a new tab, alongside the existing download link for the stored extracted text
  - [x] "Link" added to the Documents & Contracts screen's type filter, since these documents
        appear there too (same `documents` table, same list endpoint)
  - [x] Verified past "no error thrown": (1) real fetch against a real live webpage
        (anthropic.com/news) returned real title + 7516 chars of real extracted text; (2) SSRF
        guard tested against 4 real unsafe targets (localhost, 127.0.0.1, the AWS/GCP metadata IP
        169.254.169.254, a private 192.168.x address) — all 4 correctly blocked with a clear error,
        zero false negatives; (3) full real browser test: pasted a real URL into a selected deal's
        Sources panel, got back a real new document with the page's real title, a working download
        link, and a working "open source" link, zero console errors; (4) confirmed the stored
        link-document is fully readable through `fetch_document`/`build_content_block()` — same
        pipeline any uploaded file uses, not a separate weaker path. Cleaned up all self-created
        test documents (both a curl-created one and two from Playwright test runs) afterward.
