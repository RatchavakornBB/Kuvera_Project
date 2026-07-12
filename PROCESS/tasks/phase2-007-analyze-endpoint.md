Scope: backend/app/routes/analyze.py, backend/app/services/analyze.py, backend/app/main.py, backend/app/services/documents.py (extend — save summary back to the document row)
Depends on: phase2-006-graph (done)
Files allowed to touch: files listed above
DoD:
  - [x] Cross-package import (backend calling agents/) solved explicitly (deferred from D-007) — documented, not a hack left unexplained (D-009)
  - [x] POST /deals/{id}/analyze triggers the full Analyst Lead subgraph synchronously, returns summary/risk_flags/ic_memo_draft/pricing_note
  - [x] Result persisted via agents.analyses.save_analysis() so future contradiction checks and Deal Detail (later phases) have it; documents.summary kept current too
  - [x] On a real node failure, the endpoint surfaces which node/attempt/error explicitly (AGENT.md Section 10) rather than a generic 500 — except pricing_advisor, whose failure only omits pricing_note per the invariant. Found and fixed a real bug this exposed: fetch_document() calls were outside with_retry in both doc_summarizer and risk_flagger, so a real failure leaked past NodeFailure entirely as a generic 500. Fixed by wrapping the full node body in with_retry, not just the model call.
  - [x] Full end-to-end HTTP test: uploaded a real document, POST /analyze, inspected the real response (twice — before and after the retry-boundary fix, to confirm no regression) — not a unit test with mocked nodes. Also tested 404 (nonexistent deal) and the NodeFailure error path (nonexistent document) for real.
