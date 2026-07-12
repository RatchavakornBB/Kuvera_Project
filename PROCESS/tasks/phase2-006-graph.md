Scope: agents/graph.py, agents/config.py (extend), .env / .env.example (DATABASE_URL), backend/requirements.txt
Depends on: phase2-005-ic-memo-pricing (done)
Files allowed to touch: files listed above
DoD:
  - [x] Real LangGraph StateGraph: gate (doc_summarizer -> risk_flagger, plain edge) + Send() fan-out (risk_flagger -> [ic_memo_drafter, pricing_advisor] in parallel), matching Figure 4
  - [x] Checkpointer is Supabase Postgres from day one (AGENT.md Section 1) — never in-memory
  - [x] Full graph run verified end to end through the real LangGraph engine (not just calling node functions directly) — all 4 nodes' outputs present in final merged state, no key-conflict errors from the parallel fan-out
  - [x] Checkpoint rows actually persisted in Postgres — verified by querying the checkpoints table directly (5 rows for the test thread_id), not assumed from "no error was raised"
