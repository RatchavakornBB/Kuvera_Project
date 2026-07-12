Scope: agents/nodes/ic_memo_drafter.py, agents/nodes/pricing_advisor.py
Depends on: phase2-004-risk-flagger (done — summary + risk_flags available in state)
Files allowed to touch: files listed above
DoD:
  - [x] ic_memo_drafter produces a real markdown IC memo from summary + risk_flags (core deliverable — failure propagates as a real NodeFailure, not swallowed)
  - [x] pricing_advisor produces a pricing_note when data supports it — explicitly secondary (AGENT.md Section 10 / Section 11 invariant): its failure must never block or degrade ic_memo_drafter's output, only omit pricing_note. Also correctly declines to invent a number when data quality doesn't support one, suggesting structural protections instead — matches the prompt's explicit instruction, not a fluke.
  - [x] Both nodes return partial state updates (not `{**state, ...}`) since they'll run concurrently under Send() fan-out — spreading the full state would make both write every pre-existing key in the same superstep
  - [x] Both verified standalone against real Deal A data (summary + risk_flags already produced by 3.1/3.2) — 3,724-character IC memo, well-reasoned pricing note
