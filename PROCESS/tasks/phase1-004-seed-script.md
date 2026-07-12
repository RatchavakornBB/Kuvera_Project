Scope: supabase/seed.sql
Depends on: phase1-003-migrations (done — 8-table schema live)
Files allowed to touch: supabase/seed.sql only
DoD:
  - [x] Single seeded demo user (system-architecture.md Section 4.4) — auth.users + auth.identities + matching public.users profile row
  - [x] "Deal A" worked example seeded exactly per system-architecture.md Section 3.3: stage = Due Diligence, contact Khun A, document "FY2025 audited financial statements" requested, milestone "NDA signed", task "Financial model" pending
  - [x] 2 additional demo deals at different stages/statuses for dashboard variety (Section 6 Phase 1: "2-3 example deals")
  - [x] Runs automatically on `supabase db reset` (via config.toml's `[db.seed] sql_paths`), no manual extra step
  - [x] Verified with a real query (curl/psql/supabase-py), not just "the SQL ran without error" — rows actually present with correct values
  - [x] Demo user can actually sign in (`sign_in_with_password`), not just exist as a row — caught and fixed a GoTrue schema gotcha (D-006)
