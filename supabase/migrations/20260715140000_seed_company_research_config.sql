-- Registers agents/company_research.py (Section 10.1's "Company Insight" slot — the
-- knowledge_base.category check constraint has included 'company_insight' since the table's first
-- migration, never written until now) and adds the partial index its "current row for this deal"
-- lookup needs — the existing knowledge_base_current_idx is keyed on (industry, company_name), which
-- doesn't serve a source_deal_id-keyed lookup.

insert into public.agent_configs (agent_name, model_id)
values ('company_research', 'claude-sonnet-5')
on conflict (agent_name) do nothing;

create index knowledge_base_current_by_deal_idx
  on public.knowledge_base(category, source_deal_id)
  where superseded_at is null;
