-- Adds trajectory-aware eval case fields (agents/evals.py's TRAJECTORY_AGENTS path) on top of
-- eval_cases' existing prompt/criteria shape. All three nullable so every existing row (and
-- every existing single-shot EVAL_CASES fixture, which never sets these) is unaffected — a case
-- only runs through the new trajectory-grading path in run_eval() if its agent_name is loop-
-- enabled AND at least one of expected_tool_sequence/trajectory_rubric is set.

alter table public.eval_cases
  add column expected_tool_sequence jsonb,
  add column trajectory_rubric text,
  add column max_iterations int;
