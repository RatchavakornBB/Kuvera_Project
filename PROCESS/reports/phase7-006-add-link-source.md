## Result: ✅ DoD met — real NotebookLM-style URL sources, with real SSRF protection

Gate: real fetch against a live external page ✅ · SSRF guard tested against 4 real unsafe targets,
zero false negatives ✅ · full real browser flow verified ✅ · link-documents proven analyzable
through the existing pipeline, not a lesser stub ✅.

User asked whether Sources could support adding a link, like NotebookLM. Since this app's document
model is deal-scoped (every document belongs to exactly one deal — a structural fact, not a
limitation to work around), the natural, consistent placement was inside a selected deal's expanded
Sources view (built moments earlier in phase7-005): paste a URL, it becomes a real document for
that deal.

**Built a real fetch-and-extract pipeline, not a bookmark/citation stub.** `agents/web_source.py`
does a real server-side HTTP fetch (httpx) and extracts real readable text via BeautifulSoup
(strips `<script>`/`<style>`, keeps only visible text) — this is the page's own actual content,
not an AI-generated paraphrase. Verified against a real live URL
(anthropic.com/news/claude-3-5-sonnet): real title, 7516 characters of real extracted text.

**Took the SSRF risk seriously rather than skipping it.** This endpoint fetches arbitrary
user-supplied URLs server-side — the textbook setup for a Server-Side Request Forgery
vulnerability (pointing the fetcher at localhost, an internal service, or a cloud metadata
endpoint). `_assert_public_host()` resolves the hostname and rejects private/loopback/
link-local/reserved/multicast addresses before ever connecting, and re-checks the final host after
redirects. Tested against 4 real unsafe targets — `localhost`, `127.0.0.1`,
`169.254.169.254` (the real AWS/GCP metadata service IP), and a private `192.168.x` address — all
4 correctly blocked with a clear error, zero false negatives. Documented honestly as a best-effort
mitigation appropriate for a single-user local app (doesn't validate every intermediate redirect
hop), not oversold as exhaustive.

**Link-derived documents are first-class, not a lesser citation-only stub.** Extended
`agents/documents.py::build_content_block()` with real `.txt` support (the same chokepoint
docx/PDF/image support already lives in), so a fetched page's extracted text flows through the
exact same document-reading pipeline as an uploaded file — doc_summarizer, risk_flagger, etc. can
all read it once real analysis is triggered. Verified this directly (bypassing the currently
credit-exhausted Claude API): created a real link document, fetched it back through
`fetch_document()`/`build_content_block()`, confirmed a correct `text` block with the real page
content, no separate/weaker code path.

**Storage reuses the exact real write path** a file upload already uses
(`upload_document()`, extended with an optional `source_url` parameter) — Storage object + DB row
together, same embed-on-upload behavior, same AGENT.md Section 11 invariant. A new
`documents.source_url` column tracks real provenance (NULL for ordinary uploads).

**Full real browser verification**: pasted a real URL into a selected deal's expanded Sources
panel, got back a real new document row with the page's actual title, a 🔗 marker, a working
"open source" link (opens the real original URL in a new tab), and the existing download link
(fetches the stored extracted text) — zero console errors. Caught and cleaned up test artifact
duplication from an earlier test run that completed in the background after an initial
under-timed Playwright check exited early (three total self-created test link documents across a
curl test and two Playwright runs, all removed afterward).

No open deviations.
