Scope: supabase/migrations/ (analyses table), agents/analyses.py, agents/errors.py, agents/retry.py, agents/nodes/risk_flagger.py, agents/nodes/doc_summarizer.py (hardened)
Depends on: phase2-003-doc-summarizer (done)
Files allowed to touch: files listed above
DoD:
  - [x] analyses table added (new migration, not an edit to prior ones) — Analyst Lead run history, holds "last stored version" for the contradiction check
  - [x] risk_flagger produces structurally correct risk_flags (severity, description, source_excerpt) from a real Claude call
  - [x] Lightweight contradiction check: re-analyzing a deal with a changed document surfaces a visible high-severity flag naming the actual contradiction, does not silently overwrite
  - [x] Bounded retry (AGENT.md Section 10, max 2 attempts) + typed NodeFailure on both doc_summarizer and risk_flagger — found and fixed a real intermittent bug this uncovered (malformed tool_use output)
  - [x] Verified twice against real documents: once with no prior analysis (baseline, 8 flags), once with a deliberately conflicting revised document (7 flags including 1 correctly-worded contradiction flag)
