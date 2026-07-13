insert into public.agent_configs (agent_name, model_id)
values ('drafting_lead', 'claude-sonnet-5')
on conflict (agent_name) do nothing;
