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
