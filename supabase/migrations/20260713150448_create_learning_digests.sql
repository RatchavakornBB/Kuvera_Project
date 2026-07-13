-- Learning Agent (system-architecture.md Section 10.3) — "a separate background agent from
-- Knowledge Agent... continuously ingests the outside world," feeding (1) Industry/Competitor
-- Brief refresh (agents/industry_brief.py, phase6-002) and (2) proposed Skill additions "subject
-- to the same eval + admin approval gate as any other agent change" — real here: a proposal is a
-- genuine row in the existing pending_changes table (phase5-006), reviewed in the same real
-- Pending Approvals tab as a human-authored change, not a separate/weaker path.

create table public.learning_digests (
  id uuid primary key default gen_random_uuid(),
  category text not null check (category in (
    'ma_training_data', 'prediction_models', 'market_news', 'law_regulation'
  )),
  topic text not null,
  digest text not null,
  proposed_change_id uuid references public.pending_changes(id),
  created_at timestamptz not null default now()
);

create index learning_digests_category_idx on public.learning_digests(category);

grant select, insert, update, delete on public.learning_digests to service_role;

insert into public.agent_configs (agent_name, model_id)
values ('learning_agent', 'claude-sonnet-5')
on conflict (agent_name) do nothing;
