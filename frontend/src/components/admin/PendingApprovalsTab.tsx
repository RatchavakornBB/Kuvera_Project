import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchPendingApprovals, resolvePendingChange, runEvalForChange, type ApiPendingChange } from '../../lib/api';
import { DiffView } from './DiffView';

const PASS_THRESHOLD = 0.7;

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function EvalBar({ change }: { change: ApiPendingChange }) {
  const queryClient = useQueryClient();
  const [showDetail, setShowDetail] = useState(false);

  const evalMutation = useMutation({
    mutationFn: () => runEvalForChange(change.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pending-approvals'] }),
  });

  if (change.eval_pass_rate === null || change.eval_pass_rate === undefined) {
    return (
      <div className="mt-2 flex items-center gap-2">
        <button
          onClick={() => evalMutation.mutate()}
          disabled={evalMutation.isPending}
          className="cursor-pointer rounded border border-grid bg-transparent px-2.5 py-1 text-[10px] text-blue disabled:opacity-40"
        >
          {evalMutation.isPending ? 'Running eval…' : 'Run eval'}
        </button>
        {evalMutation.data?.note && <span className="text-[10px] text-gray">{evalMutation.data.note}</span>}
      </div>
    );
  }

  const pct = Math.round(change.eval_pass_rate * 100);
  const passing = change.eval_pass_rate >= PASS_THRESHOLD;

  return (
    <div className="mt-2">
      <button
        onClick={() => setShowDetail((v) => !v)}
        className="flex w-full cursor-pointer items-center gap-2 border-none bg-transparent p-0 text-left"
      >
        <div className="h-2 flex-1 overflow-hidden rounded-sm bg-terminal-black">
          <div
            className="h-full"
            style={{ width: `${pct}%`, background: passing ? 'var(--color-green)' : 'var(--color-red)' }}
          />
        </div>
        <span className={`font-mono text-[10px] ${passing ? 'text-green' : 'text-red'}`}>{pct}% eval pass rate</span>
      </button>
      {showDetail && change.eval_results && (
        <div className="mt-2 flex flex-col gap-1.5">
          {change.eval_results.map((r, i) => (
            <div key={i} className="rounded-sm border border-grid bg-terminal-black px-2 py-1.5">
              <div className={`text-[9.5px] font-semibold ${r.passed ? 'text-green' : 'text-red'}`}>
                {r.passed ? 'PASS' : 'FAIL'} — {r.criteria}
              </div>
              <div className="mt-0.5 text-[10px] text-gray">{r.reason}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function PendingApprovalsTab() {
  const queryClient = useQueryClient();
  const { data: pending, isLoading } = useQuery({
    queryKey: ['pending-approvals'],
    queryFn: fetchPendingApprovals,
  });

  const resolveMutation = useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'approve' | 'reject' }) => resolvePendingChange(id, action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] });
      queryClient.invalidateQueries({ queryKey: ['agent-configs'] });
      queryClient.invalidateQueries({ queryKey: ['audit-log'] });
    },
  });

  if (isLoading) return <div className="text-[11px] text-gray">Loading…</div>;

  if (!pending || pending.length === 0) {
    return (
      <div className="rounded border border-grid bg-panel p-4 text-[11px] text-gray">
        No pending changes — propose one from the Agents &amp; Models or Skills tab.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {pending.map((change) => (
        <div key={change.id} className="rounded border border-grid bg-panel p-4">
          <div className="mb-2 flex items-center justify-between">
            <div className="text-[11.5px] font-semibold text-white">
              {change.agent_name} <span className="text-gray">·</span>{' '}
              <span className="text-violet">{change.change_type}</span>
            </div>
            <div className="font-mono text-[10px] text-gray">{formatDateTime(change.proposed_at)}</div>
          </div>

          <DiffView oldText={change.old_value ?? ''} newText={change.new_value} />

          <EvalBar change={change} />

          <div className="mt-3 flex gap-2">
            <button
              onClick={() => resolveMutation.mutate({ id: change.id, action: 'approve' })}
              disabled={resolveMutation.isPending}
              className="cursor-pointer rounded border-none bg-green px-3 py-1.5 text-[10.5px] font-semibold text-terminal-black disabled:opacity-40"
            >
              Approve
            </button>
            <button
              onClick={() => resolveMutation.mutate({ id: change.id, action: 'reject' })}
              disabled={resolveMutation.isPending}
              className="cursor-pointer rounded border border-grid bg-transparent px-3 py-1.5 text-[10.5px] text-red disabled:opacity-40"
            >
              Reject
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
