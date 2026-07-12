## Current
Phase: 1 (Foundations)
Active task: none — phase1-004-seed-script closed
Status: idle, ready to pull next task
Last checkpoint commit: 58c8df5
Blocked on: nothing

## Next up
phase1-006-wire-dashboard — pulled from backlog.md "Ready": needs a `/deals` GET endpoint added to `/backend` first (none exists yet besides `/health`), then wire the frontend Dashboard (Board + Table view) to it, replacing `mockDeals.ts`

## Open questions for user
- none currently open

## Environment notes (read before assuming state)
- Local Supabase for this project runs on shifted ports 55321 (API), 55322 (DB), 55323 (Studio), 55324 (Inbucket/SMTP), 55327 (Analytics) — NOT the 54321 default, because an unrelated project ("foodos") already occupies those on this machine. See decisions.md D-004.
- Docker Desktop is not always running by default on this machine — check `docker ps` before assuming Supabase is up (AGENT.md Section 4).
- `.env`'s `ANTHROPIC_API_KEY` is a real key (user filled it in 2026-07-12). Never print, log, or commit its value.
- Core schema (8 tables) is live via `supabase/migrations/20260712162858_create_core_schema.sql`. Any NEW migration that adds a public table must include its own `GRANT ... TO service_role` block (D-005).
- `supabase/seed.sql` auto-runs on `supabase db reset`: 1 demo user (demo@kuvera.capital / kuvera-demo, role Partner, can actually sign in) + 3 deals (Deal A = the worked example, Horizon Freight Corp, Nova Fintech). Any future seeded `auth.users` row must set every `*_token`/`email_change*` column to `''`, not leave them NULL (D-006).
