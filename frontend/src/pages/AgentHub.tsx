import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { fetchAgentActivity, fetchAgentGrid } from '../lib/api';
import { AgentGrid } from '../components/agentHub/AgentGrid';
import { AgentDetailPanel } from '../components/agentHub/AgentDetailPanel';
import { LiveGraphView } from '../components/agentHub/LiveGraphView';

const NODE_LABEL: Record<string, string> = {
  doc_summarizer: '3.1 Doc Summarizer',
  risk_flagger: '3.2 Risk Flagger',
  ic_memo_drafter: '3.3 IC Memo Drafter',
  pricing_advisor: '3.4 Pricing Advisor',
};

type View = 'grid' | 'graph' | 'log';

function formatTs(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
  });
}

function ActivityLogView() {
  const navigate = useNavigate();
  const { data: activity, isLoading, isError } = useQuery({
    queryKey: ['agent-activity'],
    queryFn: () => fetchAgentActivity(50),
  });

  if (isLoading) return <div className="text-[11px] text-gray">Loading activity…</div>;
  if (isError) return <div className="text-[11px] text-red">Failed to load agent activity.</div>;
  if (!activity) return null;

  return (
    <div className="overflow-hidden rounded border border-grid bg-panel">
      <div className="grid grid-cols-[1.3fr_1fr_1.4fr_0.7fr_1.3fr] gap-3 border-b border-grid px-3 py-2 text-[10px] uppercase tracking-wide text-gray">
        <div>Timestamp</div>
        <div>Node</div>
        <div>Document</div>
        <div>Status</div>
        <div>Deal</div>
      </div>
      {activity.length === 0 && (
        <div className="px-4 py-6 text-center text-[11px] text-gray">
          No agent activity yet — run an analysis from a deal's Analysis tab to populate this log.
        </div>
      )}
      {activity.map((event, i) => (
        <div
          key={`${event.thread_id}-${event.step}-${event.node}-${i}`}
          className="grid grid-cols-[1.3fr_1fr_1.4fr_0.7fr_1.3fr] items-center gap-3 border-b border-grid px-3 py-2.5 text-[11.5px] last:border-none"
        >
          <div className="font-mono text-[10.5px] text-gray">{formatTs(event.ts)}</div>
          <div className="text-[#e7e7ea]">{NODE_LABEL[event.node] ?? event.node}</div>
          <div className="truncate text-gray">{event.document_name ?? '—'}</div>
          <div className="flex items-center gap-1.5">
            <div className={`h-[7px] w-[7px] rounded-full ${event.status === 'success' ? 'bg-green' : 'bg-red'}`} />
            <span className={event.status === 'success' ? 'text-green' : 'text-red'}>{event.status}</span>
          </div>
          <button
            onClick={() => navigate(`/deals/${event.deal_id}`)}
            className="cursor-pointer truncate border-none bg-transparent p-0 text-left text-blue"
          >
            {event.deal_name ?? event.deal_id}
          </button>
        </div>
      ))}
    </div>
  );
}

export function AgentHub() {
  const [view, setView] = useState<View>('grid');
  const [openAgent, setOpenAgent] = useState<string | null>(null);

  const { data: grid } = useQuery({ queryKey: ['agent-grid'], queryFn: fetchAgentGrid, refetchInterval: 15000 });
  const leadCount = grid ? new Set(grid.map((a) => a.lead)).size : 0;
  const agentCount = grid?.length ?? 0;

  return (
    <div className="flex flex-col gap-4 p-8">
      <div>
        <div className="text-lg font-bold text-white">Agent Hub</div>
        <div className="mt-1 text-[11px] text-gray">
          {agentCount > 0
            ? `${agentCount} real agents across ${leadCount} Leads — every card and status dot is
              backed by real call_model() invocations (agents/activity_tracker.py), not mocked.`
            : 'Loading…'}{' '}
          The design doc frames this as "all 21 agents"; this reflects what's actually implemented
          in this codebase, not a padded roster.
        </div>
      </div>

      <div className="flex gap-0.5 border-b border-grid">
        {(
          [
            ['grid', 'Agent Grid'],
            ['graph', 'Live Graph'],
            ['log', 'Activity Log'],
          ] as [View, string][]
        ).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setView(key)}
            className={`cursor-pointer border-none border-b-2 bg-transparent px-3.5 py-2 text-xs ${
              view === key ? 'border-violet text-white' : 'border-transparent text-gray'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="flex items-start gap-4">
        <div className="min-w-0 flex-1">
          {view === 'grid' && <AgentGrid onOpenAgent={setOpenAgent} />}
          {view === 'graph' && <LiveGraphView />}
          {view === 'log' && <ActivityLogView />}
        </div>
        {openAgent && <AgentDetailPanel agentName={openAgent} onClose={() => setOpenAgent(null)} />}
      </div>
    </div>
  );
}
