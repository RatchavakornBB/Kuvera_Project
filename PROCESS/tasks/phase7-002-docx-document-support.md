Scope: agents/documents.py
Depends on: python-docx (already a dependency since phase6-004's Drafting Lead)

Scope: user asked "ทำให้ไฟล์รองรับ Docx ได้มั้ย" (can files support .docx?). Every document-reading
node (doc_summarizer, risk_flagger, contract_summarizer, clause_extractor) previously raised
"Unsupported document type for direct model reading: .docx" — uploads always accepted any file
(no frontend restriction), but the actual analysis step failed for Word documents. Claude's
Messages API has no native .docx content block (only `document` for PDF and `image` for images),
so this is bridged honestly: real text extracted via python-docx (the same library
agents/drafting_lead.py already uses in the opposite direction, to generate .docx), sent as a
`text` content block. This is a genuine extraction of the file's actual paragraph/table text, not
a fabricated summary — same honesty standard already applied to why audio/video are NOT supported
(no real transcription pipeline exists to bridge them the same way).

DoD:
  - [x] `_MEDIA_TYPES` gains a `"docx"` entry (the real OOXML MIME type)
  - [x] `build_content_block()` handles the docx media type by extracting real text
        (`_extract_docx_text()`, via python-docx's `Document`/paragraphs/tables) and returning a
        `text` block — every existing caller (doc_summarizer, risk_flagger, contract_summarizer,
        clause_extractor) needed zero changes, since they all already just spread whatever
        `build_content_block()` returns into a content array alongside another text block
  - [x] `fetch_document()`'s error message updated to reflect the new real support (no longer
        falsely claims only PDF/images work)
  - [x] Module docstring updated to explain the real bridging technique and why it's honest
        (real extracted text, not fabricated) versus why audio/video remain genuinely unsupported
  - [x] Verified past "no error thrown": (1) extracted text directly from a real, already-existing
        .docx in the system (a Drafting-Lead-generated IC memo) and confirmed the extracted text
        matched the file's real content; (2) ran the real `doc_summarizer` node function directly
        against that file and got a real, correct, content-grounded summary; (3) full end-to-end
        test through the actual live API: generated a brand-new real .docx (via python-docx) with
        specific real financial figures, uploaded it through `POST /deals/{id}/documents`, ran
        `POST /deals/{id}/analyze` against it, and got back a real summary, real risk flags
        (correctly including a real detected contradiction against Deal A's differently-figured
        prior analysis — the contradiction engine working correctly on docx-derived content too),
        a real IC memo, and a real pricing note — the full Analyst Lead pipeline, not just the
        extraction step in isolation. Cleaned up the test document (DB row, analyses row, storage
        object) afterward as a self-created test artifact.
