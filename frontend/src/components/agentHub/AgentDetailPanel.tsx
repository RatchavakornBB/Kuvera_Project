import { useQuery } from '@tanstack/react-query';
import { fetchAgentDetail } from '../../lib/api';

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
  });
}

function Sparkline({ counts }: { counts: number[] }) {
  const max = Math.max(...counts, 1);
  return (
    <div className="flex h-8 items-end gap-1">
      {counts.map((c, i) => (
        <div
          key={i}
          className="w-3 rounded-t-sm bg-violet"
          style={{ height: `${Math.max((c / max) * 100, c > 0 ? 8 : 2)}%`, opacity: c > 0 ? 1 : 0.25 }}
          title={`${c} run(s)`}
        />
      ))}
    </div>
  );
}

export function AgentDetailPanel({ agentName, onClose }: { agentName: string; onClose: () => void }) {
  const { data: detail, isLoading } = useQuery({
    queryKey: ['agent-detail', agentName],
    queryFn: () => fetchAgentDetail(agentName),
  });

  return (
    <div className="w-[340px] shrink-0 rounded border border-grid bg-panel p-4">
      <div className="mb-3 flex items-start justify-between">
        <div>
          <div className="text-xs font-semibold text-white">{agentName}</div>
          {detail && <div className="text-[10px] text-gray">{detail.lead}</div>}
        </div>
        <button onClick={onClose} className="cursor-pointer border-none bg-transparent text-sm text-gray">
          &times;
        </button>
      </div>

      {isLoading && <div className="text-[11px] text-gray">Loading…</div>}

      {detail && (
        <>
          <div className="mb-3">
            <div className="mb-1 text-[9.5px] uppercase tracking-wide text-gray">Task volume, last 7 days</div>
            <Sparkline counts={detail.sparkline_7day} />
          </div>

          <div>
            <div className="mb-1.5 text-[9.5px] uppercase tracking-wide text-gray">Recent activity</div>
            {detail.recent_invocations.length === 0 && (
              <div className="text-[11px] text-gray">No invocations recorded yet.</div>
            )}
            <div className="flex flex-col gap-1.5">
              {detail.recent_invocations.map((inv) => (
                <div key={inv.id} className="flex items-center justify-between rounded-sm border border-grid bg-terminal-black px-2 py-1.5">
                  <span
                    className={`text-[10px] ${
                      inv.status === 'success' ? 'text-green' : inv.status === 'error' ? 'text-red' : 'text-violet'
                    }`}
                  >
                    {inv.status}
                  </span>
                  <span className="font-mono text-[9.5px] text-gray">{formatDateTime(inv.started_at)}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
