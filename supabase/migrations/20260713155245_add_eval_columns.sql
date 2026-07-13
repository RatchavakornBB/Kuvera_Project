-- Minimal real eval framework (ux-ui-spec.md Section 3.6's "Eval pass-rate bar... shown on
-- every pending approval row") — no eval framework existed anywhere in this codebase before
-- this. On-demand per pending row (an admin clicks "Run eval"), not automatic on every proposal:
-- each eval run is 2+ real Claude API calls per test case (one for the candidate output, one for
-- LLM-as-judge grading), and several agents have no eval cases defined at all yet — mandatory
-- eval-on-propose would slow down or block simple proposals for no honest benefit.

alter table public.pending_changes
  add column eval_pass_rate real,
  add column eval_results jsonb;
