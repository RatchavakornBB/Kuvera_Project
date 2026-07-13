Scope: supabase/migrations/ (documents.clauses column), agents/nodes/contract_summarizer.py, agents/nodes/clause_extractor.py, backend/app/routes/contracts.py, backend/app/services/contracts.py, backend/app/main.py
Depends on: phase2-001-documents-upload (done — upload + Storage pattern already exists)
Files allowed to touch: files listed above
DoD:
  - [x] documents.clauses jsonb column added via a new migration (not editing the core-schema migration)
  - [x] 4.1 contract_summarizer node — real Claude call, native document content block, same with_retry pattern as doc_summarizer (D-008/D-010)
  - [x] 4.2 clause_extractor node — structured tool-use output, list of {label, text}
  - [x] POST /contracts (multipart, deal_id form field) uploads to Storage + Document row (reusing the phase2-001 upload path) and runs both nodes, response: summary, clauses[]
  - [x] Verified end to end over real HTTP with a real contract fixture (synthetic Customer MSA with 6 numbered sections) — extracted 8 correctly-labeled clauses (Term & Renewal, Termination for Cause, Termination for Convenience, Change of Control, Exclusivity, Liability Cap, Indemnification, Confidentiality), all persisted to the documents row. 404 verified for a nonexistent deal.
