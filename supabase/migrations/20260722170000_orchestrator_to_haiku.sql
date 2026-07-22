-- The Orchestrator (agents/nodes/orchestrator.py) runs on every chat message purely to
-- classify it into one route — a single small tool call, no reasoning payload. Sonnet was
-- overkill: it added a full Sonnet round-trip of latency in front of every message before
-- the answering agent even started. Move it to Haiku, matching the code default in
-- agents/adapters/model_adapter.py (call_model() reads this row, so the code change alone
-- would not take effect while this seeded row still said sonnet).
update public.agent_configs
  set model_id = 'claude-haiku-4-5', updated_at = now()
  where agent_name = 'orchestrator';
