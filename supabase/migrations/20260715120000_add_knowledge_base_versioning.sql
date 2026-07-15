-- Versions the Industry/Competitor Brief cache (agents/industry_brief.py) instead of the prior
-- delete-then-insert refresh, which silently destroyed the previous Brief on every regeneration.
-- superseded_at is null for the current version of a given (category, industry) or (category,
-- company_name) scope; refreshing sets it on the old row(s) rather than deleting them, so a past
-- Brief stays queryable for audit ("the Brief said X as of date Y").

alter table public.knowledge_base add column superseded_at timestamptz;

create index knowledge_base_current_idx
  on public.knowledge_base(category, industry, company_name)
  where superseded_at is null;
