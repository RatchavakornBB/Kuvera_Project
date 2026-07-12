Scope: backend/app/db.py, backend/app/services/deals.py, backend/app/routes/deals.py, backend/app/main.py, frontend/src/lib/api.ts, frontend/src/lib/dealStage.ts, frontend/src/main.tsx, frontend/src/App.tsx, frontend/src/data/mockDeals.ts (removed)
Depends on: phase1-004-seed-script (done), phase1-005-deal-card-kanban (done)
Files allowed to touch: files listed above
DoD:
  - [x] GET /deals, POST /deals, GET /deals/{id} implemented via a service layer (route → service → supabase-py), not ad-hoc queries in routes
  - [x] CORS configured so the Vite dev server (localhost:5173) can call the API (localhost:8000)
  - [x] Frontend Kanban board wired to real /deals data via TanStack Query, mockDeals.ts deleted (dead code, nothing referenced it anymore)
  - [x] StageDiagram segment-building updated to work from real fields (`stage` + `stage_entered_at`) instead of a fabricated per-index days array
  - [x] Verified end to end: curl on all 3 endpoints (200s + a real 404), real browser screenshot showing all 3 seeded deals in their correct stage columns, zero console errors
