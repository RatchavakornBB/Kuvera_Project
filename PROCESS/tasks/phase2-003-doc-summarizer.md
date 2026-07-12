Scope: agents/config.py (extend), agents/db.py, agents/state.py, agents/nodes/doc_summarizer.py
Depends on: phase2-001-documents-upload (done — real PDF already uploaded for Deal A), phase2-002-model-adapter (done)
Files allowed to touch: files listed above
DoD:
  - [x] Shared AnalystState (agents/state.py) — deal_id, document_id, summary, risk_flags, ic_memo_draft, pricing_note
  - [x] doc_summarizer fetches the real uploaded PDF from Supabase Storage and passes it to Claude as a native document content block (system-architecture.md Section 5.4), not pre-extracted text
  - [x] Tested standalone against the real uploaded Deal A PDF (timeline Section 6 Phase 2 checkpoint) — returns a real Claude-generated summary, not a mock. Output correctly picked up every planted detail: revenue figures/growth, thin margin, customer concentration, the change-of-control clause, the undisclosed related-party transaction, and the missing audited cash flow statement.
