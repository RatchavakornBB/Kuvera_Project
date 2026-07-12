# PROCESS/backlog.md — ready / blocked / deferred work

## Ready
- [ ] phase1-002-environment-setup-remainder — repo structure done (frontend); still needs: `/backend` FastAPI scaffold, `/supabase` init, `/agents` folder, `.env` with required keys, Python env. Depends on nothing, unblocked.
- [ ] phase1-003-migrations — write migrations for all 8 models (system-architecture.md Section 3.1), run `supabase db reset`. Depends on phase1-002 (supabase init).
- [ ] phase1-004-seed-script — 2–3 example deals incl. "Deal A". Depends on phase1-003.
- [ ] phase1-005-deal-card-kanban — convert Deal card (Board view) + Kanban column shell from `docs/mockups/Kuvera Capital.dc.html`. Depends on phase1-001 (Stage Diagram, design tokens) — done.
- [ ] phase1-006-wire-dashboard — wire Dashboard to real `/deals` data (Board + Table view). Depends on phase1-004 (seed data) and phase1-005 (Deal card).

## Blocked
- (none)

## Deferred (found mid-task, not in that task's scope)
- (none)
