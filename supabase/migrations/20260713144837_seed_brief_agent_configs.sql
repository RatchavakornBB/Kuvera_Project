insert into public.agent_configs (agent_name, model_id)
values
  ('industry_brief', 'claude-sonnet-5'),
  ('competitor_brief', 'claude-sonnet-5')
on conflict (agent_name) do nothing;
