-- Per-tool-call step logging for multi-step agentic loops (agents/loop_runner.py).
-- agent_invocations already gives one row per top-level run (bracketed via
-- call_model(track_invocation=False) inside the loop + one manual
-- start_invocation/finish_invocation pair around the whole loop) — this table is
-- the ordered detail underneath it: one row per tool call within that run, so a
-- run's real trajectory (what it searched, what failed, what got circuit-broken)
-- is inspectable, not just its final status.

create table public.agent_invocation_steps (
  id uuid primary key default gen_random_uuid(),
  invocation_id uuid not null references public.agent_invocations(id) on delete cascade,
  step_index int not null,
  tool_name text not null,
  tool_input jsonb not null,
  tool_output text,
  status text not null check (status in ('success', 'error', 'skipped_circuit_broken', 'skipped_duplicate')),
  created_at timestamptz not null default now()
);

create index agent_invocation_steps_invocation_id_idx on public.agent_invocation_steps(invocation_id);

grant select, insert, update, delete on public.agent_invocation_steps to service_role;
