Scope: frontend/src/components/dealDetail/RequiredDocumentsChecklist.tsx, frontend/src/components/dealDetail/DealFileLibrary.tsx, frontend/src/pages/DealDetail.tsx
Depends on: phase4-001a (done)
Files allowed to touch: files listed above
DoD:
  - [x] Required documents checklist — real dd_items (pending/received/reviewed), matching ux-ui-spec.md's "received / pending / under review" pattern
  - [x] Deal file library — real uploaded documents with AI summary preview, status chip
  - [x] Upload button actually uploads to the real POST /deals/{id}/documents endpoint, list refreshes with the new file
  - [x] Verified end to end in a real browser: uploaded the real Customer MSA fixture, watched it appear immediately in the file library (correctly showing "No AI summary yet" / Received, since it hasn't gone through /analyze yet) via TanStack Query cache invalidation, not a manual refresh
