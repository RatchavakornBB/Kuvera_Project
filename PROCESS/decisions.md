# PROCESS/decisions.md — locked decisions (ADR-style)

Append-only. Grep this file before asking the user a question — if it's answered, don't re-ask.

## D-001 — Repo hosting (2026-07-12)
Q: where does this repo live?
Decision: private GitHub repo at `https://github.com/RatchavakornBB/Kuvera_Project.git`, remote `origin` already configured by the user before PROCESS was set up.
Status: LOCKED.

## D-002 — Build order deviated from strict Phase 1 sequence (2026-07-12)
Q: Section 6 of `docs/5day-build-timeline.md` orders Phase 1 as environment/DB setup → design tokens → Stage Diagram → Deal card → Dashboard wiring. The user asked to convert the Stage Diagram mockup to React first, before Supabase/backend setup existed.
Decision: proceeded with design tokens + Stage Diagram conversion first (both now done and verified), deferring `supabase init`, migrations, and seed script. This is a reordering within Phase 1, not a scope cut — nothing on the Section 7 cut order list was skipped.
Status: LOCKED — informational only, no action needed unless it causes a real blocker (e.g. Dashboard wiring needs seeded `/deals` data, so DB setup must happen before that step).

## D-003 — Tailwind version (2026-07-12)
Q: the timeline doesn't pin a Tailwind version.
Decision: installed Tailwind CSS v4 via the `@tailwindcss/vite` plugin (CSS-first `@theme` config, no `tailwind.config.js`/PostCSS needed) rather than v3. Design tokens live in `frontend/src/styles/tokens.css`.
Status: LOCKED.

## D-004 — Local Supabase ports shifted off the 54321-54327 default (2026-07-12)
Q: `docker ps` showed an unrelated project's Supabase stack ("foodos") already running and occupying the default local Supabase ports (54321-54327). Running `supabase start` for Kuvera on default ports would conflict.
Decision: user chose to shift Kuvera's local Supabase ports rather than stop the other project's containers. `supabase/config.toml` now uses 55320-55329 (api=55321, db=55322, db.shadow=55320, db.pooler=55329, studio=55323, local_smtp=55324, analytics=55327). `.env`'s `SUPABASE_URL` is `http://127.0.0.1:55321` accordingly.
Status: LOCKED — if `docker ps` ever shows the foodos stack gone and port pressure becomes an issue, ports could be reverted to default, but no reason to do so proactively.

## D-005 — New public tables need explicit GRANTs on this Supabase CLI version (2026-07-12)
Q: after `supabase db reset` applied the core-schema migration cleanly, `supabase-py` (service_role key) got `permission denied for table deals` (code 42501) on insert — even though RLS is disabled and service_role normally bypasses RLS.
Decision: confirmed via `config.toml`'s own comment — `auto_expose_new_tables` now defaults to unset/off (matching the Supabase cloud default), so newly created public tables are no longer automatically reachable by the Data API roles (`anon`, `authenticated`, `service_role`). Fixed by adding explicit `GRANT ... ON <tables> TO service_role;` at the end of the migration (anon/authenticated intentionally not granted — no direct frontend-to-Supabase usage exists yet in Phase 1, backend goes through service_role only). Verified with a real insert/select/cascade-delete round trip through `supabase-py`, not just `\d` schema inspection.
Status: LOCKED — every future migration that adds a new `public` table must repeat this GRANT block, or PostgREST/`supabase-py` calls against it will silently 42501.

## D-006 — Seeded auth.users row needs every *_token column set to '', not NULL (2026-07-12)
Q: `supabase/seed.sql` inserts the demo user directly into `auth.users`/`auth.identities` (no app code exists yet to call the Auth Admin API). First attempt left `confirmation_token`, `recovery_token`, `email_change`, etc. unset (NULL, the column's actual default per `\d auth.users`). Sign-in then failed with a 500 and `AuthApiError: Database error querying schema`.
Decision: root-caused via `docker logs supabase_auth_<project>` (not guessed) — GoTrue's Go model scans these columns into non-nullable strings, so any NULL among `confirmation_token`, `recovery_token`, `email_change_token_new`, `email_change`, `email_change_token_current`, `phone_change`, `phone_change_token`, `reauthentication_token` breaks every password sign-in with that exact error, one column at a time as each was fixed. Fixed by setting all of them to `''` explicitly in the seed insert. Verified with a real `sign_in_with_password` call, not just "the insert didn't error."
Status: LOCKED — if `auth.users` is ever seeded again elsewhere (e.g. a second demo user), copy this exact column list.

## D-007 — agents/ has its own config.py, independent of backend/app/config.py (2026-07-12)
Q: `agents/adapters/model_adapter.py` needs `ANTHROPIC_API_KEY`. Importing `app.config` from inside `agents/` would create a cross-directory dependency (`agents` → `backend/app`) that only works if `backend` happens to be on `sys.path` — fragile, and blocks the timeline's own requirement that nodes be "tested standalone" (Section 6 Phase 2), not only from inside the FastAPI process.
Decision: `agents/config.py` is a small, independent copy of the same fail-fast pattern (reads `.env` directly, same required-key check). `agents/` and `backend/` share the same Python environment (`backend/.venv`, one `requirements.txt`) but stay import-independent of each other. Standalone node tests run as `backend/.venv/Scripts/python -c "from agents...."` from the repo root (repo root is on `sys.path` automatically for `python -c`/script invocation from that cwd).
Status: LOCKED for Phase 2. When the `/deals/{id}/analyze` endpoint needs to call agents code from inside the FastAPI process (phase2-007), that cross-package import path needs solving explicitly then — not solved yet, deliberately deferred.

## D-008 — Every node needs bounded retry + response-block-type checking, not `content[0]` (2026-07-12)
Q: risk_flagger crashed intermittently (`KeyError: 'risk_flags'`) on a real (unmocked) API call — the model's extended-thinking output occasionally left the tool_use JSON incomplete. This is likely to recur on any node using tool-use structured output, and `content[0].text` (doc_summarizer's original code) is unsafe whenever a "thinking" block can precede the text block.
Decision: built `agents/errors.py` (`NodeFailure`, typed: node/attempts/reason/raw_error, per AGENT.md Section 10) and `agents/retry.py` (`with_retry`, max 2 attempts). Every node's model call + response parsing must go through `with_retry`, and must search `response.content` for the right block `.type` rather than indexing `content[0]`. Applied to doc_summarizer and risk_flagger; raised risk_flagger's `max_tokens` 2048→4096 since thinking tokens count against the same budget as the tool call.
Status: LOCKED — ic_memo_drafter and pricing_advisor must follow the same pattern when built.

## D-009 — Cross-package import resolved via sys.path bootstrap in backend/app/main.py (2026-07-12)
Q: D-007 deferred how `backend/app` (the FastAPI process) would import `agents/`, a sibling top-level directory, not a subpackage. Two options existed: (a) always launch uvicorn from the repo root with `--app-dir backend` (adds both the repo root and `backend` to `sys.path` — tested, works), or (b) a code-level `sys.path` bootstrap in `main.py`.
Decision: went with (b) — `backend/app/main.py` inserts the repo root into `sys.path` before importing anything that needs `agents`, so the app works correctly regardless of the launch directory/flags used. Chosen over relying on a specific CLI invocation because forgetting `--app-dir backend` fails silently in a way that's easy to hit again in a live demo — the app-level fix removes that foot-gun entirely.
Status: LOCKED.

## D-010 — with_retry must wrap the ENTIRE node body, not just the model call (2026-07-12)
Q: phase2-007's end-to-end failure test (nonexistent document_id) returned a generic unhelpful 500 instead of the expected structured NodeFailure error, despite `with_retry` existing in both doc_summarizer and risk_flagger.
Decision: root cause was `fetch_document()` (and in risk_flagger, also `get_last_analysis()`) being called *outside* the `with_retry(...)` lambda — only the model call + response parsing were protected. Fixed by moving those calls inside the retried callable in both nodes. Verified by re-running the exact same failing request and confirming the proper `{node, attempts, reason, raw_error}` body came back, then re-ran the happy path to confirm no regression.
Status: LOCKED — every future node must wrap its full body (every fallible step: fetches, model calls, parsing) in a single `with_retry(...)` call, never just the model-call portion.
