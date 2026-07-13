## Result: ✅ Real bug found and fixed

Found while auditing every node's data-access pattern at the user's explicit request (checking how
each sub-agent accesses Skill/KB/files, and whether nodes match spec). `POST /deals/{deal_id}/analyze`
accepted a `document_id` in its request body independent of the `deal_id` path parameter and never
verified the two were related — only that the deal itself existed. `agents/documents.py`'s
`fetch_document()` fetches whatever `document_id` it's given with no deal_id check of its own, and
`analyze_service.run_analysis()` saves the result under the *path's* `deal_id` regardless of which
deal the document actually belongs to.

This is a real, not hypothetical, violation of AGENT.md Section 11 ("never blend data across
deals") — reproduced before fixing: uploaded a real document to Horizon Freight Corp, then called
`POST /deals/{Deal A id}/analyze` with that document's ID; it would have analyzed Horizon Freight
Corp's document and saved the result into Deal A's `analyses` table.

Fix: added `documents_service.get_document(document_id)`; the route now checks
`document["deal_id"] == deal_id` and returns 404 before touching the LLM pipeline at all. Verified
with real HTTP calls (not just re-reading the code): the same cross-deal request now 404s
("Document not found for this deal"), and the legitimate same-deal request (Horizon Freight Corp's
own document, Horizon Freight Corp's own analyze endpoint) still runs the real Analyst Lead
pipeline successfully.

Side effect kept, not cleaned up: Horizon Freight Corp now has one real uploaded/analyzed document
(`deal_a_customer_msa.pdf`, re-used as a convenient real PDF fixture) from this verification —
harmless, and consistent with this session's established precedent of keeping real test-created
data rather than risking an unreviewed direct-DB deletion. Flagged for the user in case the "Horizon
Freight Corp has zero documents" empty-state example in `docs/demo-script.md` needs updating.

Other finding from the same audit, not a bug, logged for awareness: `agents/nodes/web_research.py`
calls `call_model("orchestrator", ...)` rather than having its own `AGENT_MODELS`/`agent_configs`
entry, so the Admin & Skill Governance screen's "orchestrator" agent config affects both the chat
intent-classification call and the web-research answering call together. Not fixed — it's a real
architectural coupling, not a correctness bug, and splitting it is a design decision outside this
audit's scope.
