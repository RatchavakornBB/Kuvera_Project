Scope: supabase/migrations/
Depends on: phase1-002-environment-setup-remainder (done — local Supabase running)
Files allowed to touch: supabase/migrations/ only
DoD:
  - [x] All 8 models from system-architecture.md Section 3.1 exist as tables: Deal, Contact, Document, Task, MeetingNote, DDItem, Milestone, User
  - [x] Foreign keys to Deal throughout (per timeline Section 4.3), `on delete cascade` so deleting a deal cleans up its child rows
  - [x] Deal stage matches the 7-stage list in system-architecture.md Section 3.2 exactly
  - [x] `supabase db reset` runs clean, schema visible via `docker exec` psql query (Supabase Studio UI not checked headlessly, but table existence + columns verified via SQL)
  - [x] RLS left disabled for Phase 1 — full RBAC is explicitly Phase 3 scope (system-architecture.md Section 1.4), logged as a decision, not silently skipped
  - [x] Real insert/select/cascade-delete round trip verified through `supabase-py` (service_role), not just schema DDL — caught and fixed a Data API permission gap (D-005)
