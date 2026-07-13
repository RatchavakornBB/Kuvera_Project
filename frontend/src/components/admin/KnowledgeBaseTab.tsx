import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  fetchKnowledgeRecords,
  searchKnowledgeRecords,
  type ApiKnowledgeRecord,
} from '../../lib/api';

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
          <option value="Healthcare">Healthcare</option>
          <option value="Logistics">Logistics</option>
          <option value="Fintech">Fintech</option>
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
        Detail header to populate this. Industry/Competitor Insight aren't populated: they'd need a
        periodically-refreshed cross-deal Brief, which needs an outside-world monitoring pipeline
        not built in this MVP.
      </div>

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
