Scope: backend/app/routes/analyze.py, backend/app/services/documents.py
Depends on: none — found during a user-requested audit of node data-access patterns
Files allowed to touch: files listed above

Bug found: `POST /deals/{deal_id}/analyze` never verified that the `document_id` in its request
body actually belongs to `deal_id`. It only checked the deal exists, then ran the Analyst Lead
against whatever document_id was given and saved the result under the URL's deal_id — a real
violation of AGENT.md Section 11's "never blend data across deals" invariant, not a hypothetical
one (verified via a real cross-deal `curl` call before the fix, which succeeded and would have
attributed one deal's document analysis to another deal's `analyses` history).

DoD:
  - [x] `documents_service.get_document(document_id)` added
  - [x] `POST /deals/{deal_id}/analyze` returns 404 if the document doesn't exist or belongs to a
        different deal, before running any real LLM call
  - [x] Verified with real HTTP calls: uploaded a real document to Horizon Freight Corp, confirmed
        analyzing it via Deal A's endpoint now 404s, confirmed analyzing it via Horizon Freight
        Corp's own endpoint still works (real analysis kicked off successfully)
