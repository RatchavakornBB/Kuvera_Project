Scope: supabase/migrations/ (storage bucket), backend/app/services/documents.py, backend/app/routes/documents.py, backend/app/main.py
Depends on: phase1-003-migrations (done), phase1-004-seed-script (done)
Files allowed to touch: files listed above
DoD:
  - [x] Storage bucket for deal documents exists (created via migration, reproducible on `supabase db reset`)
  - [x] POST /deals/{id}/documents (multipart) uploads to Supabase Storage AND creates a Document row together (AGENT.md Section 11 invariant — never one without the other)
  - [x] Uploading a real PDF creates a real storage object and DB row — verified by downloading the object back and checking the `%PDF` magic bytes, not just "the code compiles"
