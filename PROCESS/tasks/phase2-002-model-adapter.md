Scope: agents/adapters/model_adapter.py
Depends on: phase1-002-environment-setup-remainder (done — ANTHROPIC_API_KEY in .env)
Files allowed to touch: agents/adapters/model_adapter.py only
DoD:
  - [x] Single call_model(agent_name, messages, tools=[]) function per AGENT.md Section 1 / timeline Section 5.1
  - [x] Looks up agent_name's model_id from a config dict, dispatches to the right client — no node will ever call `anthropic.Anthropic()` directly
  - [x] A real call against the live Anthropic API succeeds (not mocked) — proves the adapter, the API key, and the model ID are all actually correct
