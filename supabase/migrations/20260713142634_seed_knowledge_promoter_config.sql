-- knowledge_promoter (agents/knowledge.py) is a real call_model() caller like every other
-- agent — give it a real agent_configs row so it's governable from the Admin & Skill
-- Governance screen too, not a silent exception to the pattern.
insert into public.agent_configs (agent_name, model_id)
values ('knowledge_promoter', 'claude-sonnet-5')
on conflict (agent_name) do nothing;
