Scope: backend/app/services/documents.py
Depends on: phase7-006 (add-link source), agents/nodes/doc_summarizer.py (Phase 2),
agents/deal_context.py (Phase 3)

Scope: user asked whether the Agent can actually read a link source after adding it. Traced the
real code path: `agents/deal_context.py::build_deal_context()` — what Concierge Q&A actually
reads — only ever surfaces a document's `summary` field (truncated to 200 chars), never raw
document bytes. `create_document_from_url()` (phase7-006) only created the document row; nothing
auto-triggered summarization, so a freshly-added link sat with `summary: null` and was invisible
to Concierge until someone separately ran Analyze on it. This didn't match NotebookLM's real
behavior (sources are immediately queryable once added) and didn't match user expectations.

DoD:
  - [x] `create_document_from_url()` now runs a real `doc_summarizer` call immediately after
        creating the document — just that one node, not the full Analyst Lead pipeline
        (risk-flagging/IC-memo/pricing don't make sense for a general reference URL), then stores
        the result via the existing `update_document_summary()` path (also re-embeds on the
        stronger name+summary text, same as any other document)
  - [x] Best-effort: a summarization failure doesn't fail the whole add-link action — the document
        was already created successfully; it just leaves `summary` null the same as any
        never-analyzed document, no regression from pre-fix behavior
  - [x] Verified past "no error thrown" — with real Anthropic API credits restored mid-task:
        (1) real live add-link call (real fetch + real Voyage embed + real Claude summarization)
        completed in ~35.8s and returned a real, detailed, correctly-grounded summary (identified
        the page as a marketing announcement, extracted real pricing figures, flagged real
        diligence concerns like unaudited self-reported benchmarks); (2) confirmed via
        `build_deal_context()` directly that the new summary is now genuinely included in
        Concierge's real context, not just stored inertly; (3) full real end-to-end test: asked
        Concierge a real question about the link's content — it correctly referenced the document
        and, since only a 200-char preview reaches it (a pre-existing, deal-context-wide
        characteristic applying to every document type, not link-specific), correctly declined to
        guess at details beyond that preview rather than fabricating an answer, an honest result;
        (4) real browser test confirming the UI shows a pending state during the longer
        (~35s) summarization wait and the new source renders correctly once done, zero console
        errors
