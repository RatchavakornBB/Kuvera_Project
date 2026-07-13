-- Real, uniform activity tracking for the Agent Hub full view (ux-ui-spec.md Section 3.5).
-- Before this, only the 4 Analyst Lead nodes had any activity trail at all (reconstructed from
-- LangGraph's own Postgres Checkpointer, agents/activity_log.py, phase4-003) — every other real
-- agent built since (Concierge, Orchestrator, Contracts Lead, Knowledge Agent, Learning Agent,
-- Drafting Lead) had no status signal whatsoever. call_model() — the one real chokepoint every
-- agent already goes through — now logs a real row on every invocation: 'running' the moment the
-- call starts, updated to 'success'/'error' when it finishes. This is what makes a real "live"
-- status dot and a real 7-day sparkline possible without fabricating either.

create table public.agent_invocations (
  id uuid primary key default gen_random_uuid(),
  agent_name text not null,
  status text not null default 'running' check (status in ('running', 'success', 'error')),
  error_reason text,
  started_at timestamptz not null default now(),
  completed_at timestamptz
);

create index agent_invocations_agent_name_idx on public.agent_invocations(agent_name);
create index agent_invocations_started_at_idx on public.agent_invocations(started_at);

grant select, insert, update, delete on public.agent_invocations to service_role;
