-- Registers the new contracts_lead agentic-loop identity (agents/contracts_graph.py)
-- so it's governable through the existing Admin & Skill Governance flow like every
-- other agent — model swap, skill.md edits, eval pass-rate, all for free. The old
-- single-shot contract_summarizer/clause_extractor agent_configs rows stay as-is;
-- they're kept as regression coverage of the underlying capability even though the
-- live contract-analysis path no longer calls them directly.

insert into public.agent_configs (agent_name, model_id)
values ('contracts_lead', 'claude-sonnet-5')
on conflict (agent_name) do nothing;
