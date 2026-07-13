Scope: agents/documents.py, agents/nodes/doc_summarizer.py, agents/nodes/risk_flagger.py,
agents/nodes/contract_summarizer.py, agents/nodes/clause_extractor.py
Depends on: phase5-006 (done) — user asked to extend file support after the KB/file-access audit
Files allowed to touch: files listed above

Scope decision (confirmed with user): extend real, honest file support to images (PNG/JPG/JPEG/
GIF/WEBP) via Claude's native `image` content block — Claude's Messages API genuinely supports
vision input, so this is a real capability, not a stub. Audio and video are explicitly NOT
extended: Claude's Messages API has no native audio/video content block as of this build (unlike
image, which Claude reads natively) — claiming to support them would mean either silently failing
or fabricating a transcription/frame-extraction pipeline that doesn't exist. `fetch_document()`
continues to raise a clear error for audio/video, now with an accurate reason (still unsupported by
the provider, not "not implemented yet" as if it were just missing glue code).

DoD:
  - [x] `agents/documents.py`: `_MEDIA_TYPES` includes real image MIME types; new
        `build_content_block(content, media_type)` helper returns the correct Claude content block
        shape (`type: "document"` for PDF, `type: "image"` for images) — single source of truth,
        not duplicated per node
  - [x] All 4 document-reading nodes (doc_summarizer, risk_flagger, contract_summarizer,
        clause_extractor) use the shared helper instead of hardcoding `type: "document"`
  - [x] Verified end to end with a real image: uploaded a real image file to a deal, ran the real
        Analyst Lead against it, confirmed Claude's actual response describes the image's real
        content (proves Claude received real vision input, not a text stub or an error swallowed
        into a generic summary)
  - [x] Verified audio/video still fail with a clear, accurate error (not silently mishandled)
