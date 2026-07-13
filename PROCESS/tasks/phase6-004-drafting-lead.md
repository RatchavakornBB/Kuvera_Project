Scope: backend/requirements.txt, agents/drafting_lead.py, agents/adapters/model_adapter.py,
supabase/migrations/<new>, backend/app/services/documents.py, backend/app/routes/documents.py,
backend/app/services/drafting.py, backend/app/routes/drafting.py, backend/app/main.py,
frontend/src/lib/api.ts, frontend/src/components/dealDetail/DraftingLeadPanel.tsx,
frontend/src/components/dealDetail/AnalysisTab.tsx, frontend/src/components/dealDetail/DealFileLibrary.tsx,
frontend/src/components/documents/DocumentDetailPanel.tsx
Depends on: real analysis data (ic_memo_drafter/risk_flagger output) — drafts from the latest
stored analysis, same as the rest of the Analyst Lead surface.

Scope, per system-architecture.md Section 9: 5.1 Doc/email prep (.docx + cover email draft, scope-
extended per Section 10.3 to a NotebookLM-style source-cited summary) and 5.2 Presentation prep
(.pptx). Real files via python-docx/python-pptx (new dependencies, no API key needed), real
Storage upload + Document row together (the same invariant every other upload path in this
codebase follows), not a decorative "export" button producing nothing durable.

Found and fixed a real pre-existing gap while building this: no document download mechanism
existed anywhere in the app — documents could be uploaded but never retrieved. Without fixing
this, Drafting Lead's output would have been unusable (generated files sitting in Storage with no
way to get them out). Added a real backend-mediated download endpoint (the Storage bucket is
private by design — no direct public URLs, per its own migration's note) and wired download links
into both places documents are listed (Deal Detail's file library, Documents & Contracts' detail
panel).

DoD:
  - [x] python-docx / python-pptx installed and added to requirements.txt
  - [x] `agents/drafting_lead.py`: real .docx (markdown-lite rendering of the real IC memo draft,
        not raw text with visible ** and #), real .pptx (title/summary/risk-flags/pricing slides
        built from real analysis data), real cover email draft, real source-cited summary (built
        directly from risk_flags' real source_excerpts, not new fabricated citations)
  - [x] `GET /documents/{id}/download` — backend-mediated, real file bytes, correct
        Content-Type/Content-Disposition
  - [x] `POST /deals/{id}/draft/{memo,deck,email,summary}`
  - [x] Frontend: `DraftingLeadPanel` on the Analysis tab (4 actions), download links added to the
        Deal Detail file library and the Documents & Contracts detail panel
  - [x] Verified end to end: generated files re-opened with python-docx/python-pptx to confirm
        they're genuinely valid Office documents (not just non-empty bytes) — correct heading,
        real bold formatting, 4 correctly-titled slides; downloaded a real memo via curl and
        confirmed via `file` that it's a genuine "Microsoft Word 2007+" document; full real
        browser session confirmed all 4 actions work and the generated file appears with a working
        download link in the file library, zero console errors
