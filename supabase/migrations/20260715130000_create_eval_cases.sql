-- Admin-authored eval test cases (agents/eval_cases.py) — the DB-backed input path for the
-- eval framework (agents/evals.py), layered on top of that file's built-in EVAL_CASES fixtures.
-- Lets an admin add a real eval case for any agent from the Admin > Eval Cases tab without a
-- code change; run_eval() reads both sources and merges them per agent_name.

create table public.eval_cases (
  id uuid primary key default gen_random_uuid(),
  agent_name text not null,
  prompt text not null,
  criteria text not null,
  created_at timestamptz not null default now()
);

create index eval_cases_agent_name_idx on public.eval_cases(agent_name);

grant select, insert, update, delete on public.eval_cases to service_role;
