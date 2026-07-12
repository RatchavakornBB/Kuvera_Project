## Current
Phase: 1 (Foundations)
Active task: none — phase1-002-environment-setup-remainder closed
Status: idle, ready to pull next task
Last checkpoint commit: 0c1e9e0
Blocked on: nothing

## Next up
phase1-003-migrations — pulled from backlog.md "Ready": write migrations for all 8 models (system-architecture.md Section 3.1), run `supabase db reset`

## Open questions for user
- none currently open

## Environment notes (read before assuming state)
- Local Supabase for this project runs on shifted ports 55321 (API), 55322 (DB), 55323 (Studio), 55324 (Inbucket/SMTP), 55327 (Analytics) — NOT the 54321 default, because an unrelated project ("foodos") already occupies those on this machine. See decisions.md D-004.
- Docker Desktop is not always running by default on this machine — check `docker ps` before assuming Supabase is up (AGENT.md Section 4).
- `.env` has a placeholder `ANTHROPIC_API_KEY` (`REPLACE_ME_before_phase2_real_claude_calls`) — must be swapped for a real key before Phase 2 Claude calls work.
