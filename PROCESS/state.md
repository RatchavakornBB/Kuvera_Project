## Current
Phase: 2 (Core AI Loop) — COMPLETE
Active task: none
Status: idle, ready to pull next task
Last checkpoint commit: be66b7c (report/decision updates for phase2-007 not yet committed — next commit)
Blocked on: nothing

## Next up
Nothing pulled yet — several Phase 3/4 items added to backlog.md "Ready" (Contracts
Lead, Concierge Q&A, Chat panel + WebSocket, web_search/EDGAR, Deal Detail, Agent Hub).
Ask the user which to prioritize rather than guessing — Phase 3 has more independent
sub-tracks than Phase 1/2 did.

## Open questions for user
- Which Phase 3/4 item to do next (see backlog.md "Ready") — not asked yet as of this
  checkpoint.

## Environment notes (read before assuming state)
- Local Supabase for this project runs on shifted ports 55321 (API), 55322 (DB), 55323 (Studio), 55324 (Inbucket/SMTP), 55327 (Analytics) — NOT the 54321 default (D-004).
- Docker Desktop is not always running by default on this machine — check `docker ps` before assuming Supabase is up (AGENT.md Section 4). After any `supabase db reset`, wait for all containers to show `(healthy)` before hitting Storage — a 502 right after reset is the storage container not ready yet, not a real bug.
- `.env` has real ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY, and DATABASE_URL (direct Postgres connection string, for the LangGraph Postgres Checkpointer only — added in Phase 2). Never print, log, or commit any of these values.
- Core schema: 10 tables now (the original 8 + `analyses` for Analyst Lead run history + Storage's own tables). Every new `public` table migration needs its own `GRANT ... TO service_role` block (D-005) — PostgREST doesn't auto-expose new tables on this Supabase CLI version.
- `supabase/seed.sql`: demo user (demo@kuvera.capital / kuvera-demo, Partner, can sign in) + 3 deals (Deal A, Horizon Freight Corp, Nova Fintech). Seeded auth.users rows need every `*_token`/`email_change*` column set to `''` (D-006).
- Backend (`backend/app/`): `/health`, `/deals` (GET/POST), `/deals/{id}` (GET), `/deals/{id}/documents` (POST, multipart upload), `/deals/{id}/analyze` (POST, runs the full Analyst Lead graph synchronously, ~45s). Service layer per resource in `app/services/`. CORS open to `http://localhost:5173` only. Launch with `sys.path` self-bootstrapping (D-009) so it works from any launch directory.
- Agents (`agents/`): standalone package, own `config.py`/`db.py` (D-007), shared bounded-retry infra in `errors.py`/`retry.py` (D-008, D-010 — every node must wrap its FULL body in `with_retry`, not just the model call). Nodes: `doc_summarizer`, `risk_flagger` (+ lightweight contradiction check against `analyses` table), `ic_memo_drafter` (core, failure propagates), `pricing_advisor` (secondary, catches its own NodeFailure and degrades to `pricing_note=None`). `graph.py` compiles the gate (3.1→3.2) + Send() fan-out (3.2→[3.3,3.4]) with the Postgres Checkpointer — its tables (`checkpoints` etc.) are created lazily by `PostgresSaver.setup()` on first graph run, NOT by a migration, so they won't exist right after a fresh `db reset` until the graph actually runs once.
- Frontend Dashboard (Board/Kanban) wired to real `/deals` data via TanStack Query. Table/Pipeline view, Chat, Deal Detail, Documents & Contracts, Agent Hub, Admin screens are all still design-only per the mockup — none built yet.
