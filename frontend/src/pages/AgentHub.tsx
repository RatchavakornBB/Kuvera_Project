import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { fetchAgentActivity } from '../lib/api';

const NODE_LABEL: Record<string, string> = {
  doc_summarizer: '3.1 Doc Summarizer',
  risk_flagger: '3.2 Risk Flagger',
  ic_memo_drafter: '3.3 IC Memo Drafter',
  pricing_advisor: '3.4 Pricing Advisor',
};

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

export function AgentHub() {
  const navigate = useNavigate();
  const { data: activity, isLoading, isError } = useQuery({
    queryKey: ['agent-activity'],
    queryFn: () => fetchAgentActivity(50),
  });

  return (
    <div className="flex flex-col gap-4 p-8">
      <div>
        <div className="text-lg font-bold text-white">Agent Hub</div>
        <div className="mt-1 text-[11px] text-gray">
          A real trace of Analyst Lead node runs, reconstructed from the LangGraph Postgres
          Checkpointer — not a live graph view (deferred to the full product; see
          ux-ui-spec.md Section 3.5 vs. the MVP scope table).
        </div>
      </div>

      {isLoading && <div className="text-[11px] text-gray">Loading activity…</div>}
      {isError && <div className="text-[11px] text-red">Failed to load agent activity.</div>}

      {activity && (
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
              No agent activity yet — run an analysis from a deal's Analysis tab to populate this
              log.
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
      )}
    </div>
  );
}
