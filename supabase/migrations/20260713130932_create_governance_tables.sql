-- Admin & Skill Governance (system-architecture.md Section 11, ux-ui-spec.md Section 3.6) —
-- the "real-scoped" build requested after this screen was originally logged as design-only
-- (5day-build-timeline.md's MVP-vs-Full-Product table). agent_configs is read by
-- agents/adapters/model_adapter.py's call_model() on every real LLM invocation, so an approved
-- change here genuinely changes agent behavior on the next call — not a decorative admin UI.

create table public.agent_configs (
  id uuid primary key default gen_random_uuid(),
  agent_name text not null unique,
  model_id text not null,
  skill_content text not null default '',
  updated_at timestamptz not null default now()
);

create table public.pending_changes (
  id uuid primary key default gen_random_uuid(),
  agent_name text not null,
  change_type text not null check (change_type in ('model_id', 'skill_content')),
  old_value text,
  new_value text not null,
  status text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
  proposed_at timestamptz not null default now(),
  reviewed_at timestamptz
);

create table public.audit_log (
  id uuid primary key default gen_random_uuid(),
  agent_name text not null,
  change_type text not null,
  old_value text,
  new_value text not null,
  action text not null check (action in ('approved', 'rejected')),
  created_at timestamptz not null default now()
);

create index pending_changes_status_idx on public.pending_changes(status);

-- Seed one row per agent currently wired up in AGENT_MODELS (agents/adapters/model_adapter.py) —
-- if this list and that dict drift apart, the Agents & Models tab is the signal to reconcile them.
insert into public.agent_configs (agent_name, model_id) values
  ('doc_summarizer', 'claude-sonnet-5'),
  ('risk_flagger', 'claude-sonnet-5'),
  ('ic_memo_drafter', 'claude-sonnet-5'),
  ('pricing_advisor', 'claude-sonnet-5'),
  ('contract_summarizer', 'claude-sonnet-5'),
  ('clause_extractor', 'claude-sonnet-5'),
  ('concierge_qa', 'claude-sonnet-5'),
  ('orchestrator', 'claude-sonnet-5');

grant select, insert, update, delete on public.agent_configs to service_role;
grant select, insert, update, delete on public.pending_changes to service_role;
grant select, insert, update, delete on public.audit_log to service_role;
