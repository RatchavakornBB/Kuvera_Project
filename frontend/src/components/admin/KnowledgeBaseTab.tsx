import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  fetchDeals,
  fetchKnowledgeRecords,
  refreshCompanyResearch,
  refreshCompetitorBrief,
  refreshIndustryBrief,
  searchKnowledgeRecords,
  type ApiKnowledgeRecord,
} from '../../lib/api';
import { SchedulerStatusPanel } from './SchedulerStatusPanel';

const INDUSTRIES = ['Healthcare', 'Logistics', 'Fintech'];

const CATEGORY_LABEL: Record<string, string> = {
  deal_profile: 'Deal Profile',
  industry_insight: 'Industry Insight',
  company_insight: 'Company Insight',
  competitor_insight: 'Competitor Insight',
  evaluation_approach: 'Evaluation Approach',
  analysis_approach: 'Analysis Approach',
  strategy_planning_approach: 'Strategy Planning Approach',
  outcome: 'Outcome',
  risk_signals_resolution: 'Risk Signals & Resolution',
  prompt_engineering: 'Prompt Engineering',
  loop_engineering: 'Loop Engineering',
};

function RecordCard({ record }: { record: ApiKnowledgeRecord }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded border border-grid bg-terminal-black">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full cursor-pointer items-center justify-between border-none bg-transparent px-3 py-2.5 text-left"
      >
        <div>
          <span className="text-[9.5px] font-semibold uppercase tracking-wide text-violet">
            {CATEGORY_LABEL[record.category] ?? record.category}
          </span>
          <span className="ml-2 text-[11px] text-[#e7e7ea]">{record.company_name ?? '—'}</span>
          {record.industry && <span className="ml-1.5 text-[10px] text-gray">· {record.industry}</span>}
        </div>
        {record.similarity !== undefined && (
          <span className="font-mono text-[9.5px] text-gray">match {(record.similarity * 100).toFixed(0)}%</span>
        )}
      </button>
      {open && (
        <div className="border-t border-grid px-3 py-2.5">
          <pre className="whitespace-pre-wrap break-words font-mono text-[10.5px] leading-relaxed text-gray">
            {JSON.stringify(record.content, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

function BriefRefreshForm() {
  const queryClient = useQueryClient();
  const [briefIndustry, setBriefIndustry] = useState(INDUSTRIES[0]);
  const [competitorName, setCompetitorName] = useState('');

  const industryMutation = useMutation({
    mutationFn: () => refreshIndustryBrief(briefIndustry),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['knowledge-base'] }),
  });

  const competitorMutation = useMutation({
    mutationFn: () => refreshCompetitorBrief(competitorName.trim(), briefIndustry),
    onSuccess: () => {
      setCompetitorName('');
      queryClient.invalidateQueries({ queryKey: ['knowledge-base'] });
    },
  });

  return (
    <div className="rounded border border-grid bg-panel p-3">
      <div className="mb-2 text-[10.5px] font-semibold text-white">Refresh a Brief</div>
      <div className="flex flex-wrap items-center gap-2">
        <select
          value={briefIndustry}
          onChange={(e) => setBriefIndustry(e.target.value)}
          className="rounded-sm border border-grid bg-terminal-black px-2 py-1.5 text-[11px] text-white"
        >
          {INDUSTRIES.map((i) => (
            <option key={i} value={i}>
              {i}
            </option>
          ))}
        </select>
        <button
          onClick={() => industryMutation.mutate()}
          disabled={industryMutation.isPending}
          className="cursor-pointer rounded border border-grid bg-transparent px-2.5 py-1.5 text-[10.5px] text-blue disabled:opacity-40"
        >
          {industryMutation.isPending ? 'Researching…' : 'Refresh Industry Brief'}
        </button>
        <span className="text-[10px] text-gray">or</span>
        <input
          value={competitorName}
          onChange={(e) => setCompetitorName(e.target.value)}
          placeholder="Competitor company name…"
          className="rounded-sm border border-grid bg-terminal-black px-2 py-1.5 text-[11px] text-white placeholder:text-gray"
        />
        <button
          onClick={() => competitorMutation.mutate()}
          disabled={!competitorName.trim() || competitorMutation.isPending}
          className="cursor-pointer rounded border border-grid bg-transparent px-2.5 py-1.5 text-[10.5px] text-blue disabled:opacity-40"
        >
          {competitorMutation.isPending ? 'Researching…' : 'Refresh Competitor Brief'}
        </button>
      </div>
      <div className="mt-1.5 text-[9.5px] text-gray">
        Real Claude web_search research, ~10-30s. Also runs automatically every 24h via the real
        scheduler below — this button triggers an on-demand refresh in addition to that.
      </div>
      {(industryMutation.isError || competitorMutation.isError) && (
        <div className="mt-1.5 text-[10px] text-red">
          Refresh failed: {String(industryMutation.error ?? competitorMutation.error)}
        </div>
      )}
    </div>
  );
}

function CompanyResearchRefreshForm() {
  const queryClient = useQueryClient();
  const [dealId, setDealId] = useState('');

  const dealsQuery = useQuery({ queryKey: ['deals'], queryFn: fetchDeals });

  const mutation = useMutation({
    mutationFn: () => refreshCompanyResearch(dealId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['knowledge-base'] }),
  });

  return (
    <div className="rounded border border-grid bg-panel p-3">
      <div className="mb-2 text-[10.5px] font-semibold text-white">Refresh Company Research</div>
      <div className="flex flex-wrap items-center gap-2">
        <select
          value={dealId}
          onChange={(e) => setDealId(e.target.value)}
          className="rounded-sm border border-grid bg-terminal-black px-2 py-1.5 text-[11px] text-white"
        >
          <option value="">Select a deal…</option>
          {dealsQuery.data?.map((deal) => (
            <option key={deal.id} value={deal.id}>
              {deal.name}
            </option>
          ))}
        </select>
        <button
          onClick={() => mutation.mutate()}
          disabled={!dealId || mutation.isPending}
          className="cursor-pointer rounded border border-grid bg-transparent px-2.5 py-1.5 text-[10.5px] text-blue disabled:opacity-40"
        >
          {mutation.isPending ? 'Researching…' : 'Refresh Company Research'}
        </button>
      </div>
      <div className="mt-1.5 text-[9.5px] text-gray">
        Real Claude web_search research on that deal's own target company, ~10-30s. Also runs
        automatically every 24h via the real scheduler above — this button triggers an on-demand
        refresh in addition to that.
      </div>
      {mutation.isError && (
        <div className="mt-1.5 text-[10px] text-red">Refresh failed: {String(mutation.error)}</div>
      )}
    </div>
  );
}

export function KnowledgeBaseTab() {
  const [industry, setIndustry] = useState('');
  const [category, setCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSearch, setActiveSearch] = useState('');

  const listQuery = useQuery({
    queryKey: ['knowledge-base', industry, category],
    queryFn: () => fetchKnowledgeRecords({ industry, category }),
    enabled: !activeSearch,
  });

  const searchQueryResult = useQuery({
    queryKey: ['knowledge-base-search', activeSearch, industry],
    queryFn: () => searchKnowledgeRecords(activeSearch, industry || undefined),
    enabled: !!activeSearch,
  });

  const records = activeSearch ? searchQueryResult.data : listQuery.data;
  const isLoading = activeSearch ? searchQueryResult.isLoading : listQuery.isLoading;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') setActiveSearch(searchQuery.trim());
          }}
          placeholder="Semantic search across promoted knowledge (real pgvector, press Enter)…"
          className="min-w-[260px] flex-1 rounded border border-grid bg-panel px-3 py-2 text-[11.5px] text-white placeholder:text-gray"
        />
        {activeSearch && (
          <button
            onClick={() => {
              setActiveSearch('');
              setSearchQuery('');
            }}
            className="cursor-pointer rounded border border-grid bg-transparent px-2.5 py-2 text-[10.5px] text-gray"
          >
            Clear search
          </button>
        )}
        <select
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          className="rounded border border-grid bg-panel px-2.5 py-2 text-[11.5px] text-white"
        >
          <option value="">All industries</option>
          {INDUSTRIES.map((i) => (
            <option key={i} value={i}>
              {i}
            </option>
          ))}
        </select>
        {!activeSearch && (
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="rounded border border-grid bg-panel px-2.5 py-2 text-[11.5px] text-white"
          >
            <option value="">All categories</option>
            {Object.entries(CATEGORY_LABEL).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="text-[10px] text-gray">
        Real, promoted from closed deals — not seeded or fabricated. Close a deal from its Deal
        Detail header to populate Deal Profile / Evaluation / Analysis / Outcome records. Industry,
        Competitor, and Company Insight all refresh automatically every 24h via the real scheduler
        below — the forms here trigger an on-demand refresh in addition to that.
      </div>

      <SchedulerStatusPanel />
      <BriefRefreshForm />
      <CompanyResearchRefreshForm />

      {isLoading && <div className="text-[11px] text-gray">Loading…</div>}

      {!isLoading && (!records || records.length === 0) && (
        <div className="rounded border border-grid bg-panel p-4 text-center text-[11px] text-gray">
          No knowledge records yet.
        </div>
      )}

      <div className="flex flex-col gap-2">
        {records?.map((record) => (
          <RecordCard key={record.id} record={record} />
        ))}
      </div>
    </div>
  );
}
