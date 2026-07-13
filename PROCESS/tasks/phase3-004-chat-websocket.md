Scope: agents/nodes/orchestrator.py, agents/adapters/model_adapter.py (add orchestrator to AGENT_MODELS), backend/app/routes/chat.py, backend/app/main.py
Depends on: phase3-002-concierge-qa (done)
Files allowed to touch: files listed above
DoD:
  - [x] Orchestrator routing is itself an LLM call (system-architecture.md Section 4.3), classifying intent between concierge_qa and analyst_lead
  - [x] /chat WebSocket: client sends {message, deal_id?}, server responds with the routed answer
  - [x] No deal_id -> Orchestrator asks which deal, never answers ungrounded or blends across deals (AGENT.md Section 11 invariant, extended to chat)
  - [x] Blocking agent calls run via run_in_threadpool so the WebSocket event loop isn't blocked
  - [x] Chat streaming explicitly NOT implemented — request/response over the WebSocket instead (D-012, timeline Section 7 cut order item 4, invoked deliberately, logged, not silently dropped)
  - [x] Verified with a real WebSocket client (3 real round trips): no-deal_id correctly asked which deal; a status question correctly routed to concierge_qa with a grounded, well-sourced answer; an explicit "re-run the analysis" message correctly routed to analyst_lead, ran the real graph on the deal's latest document, and returned an artifact card
