import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchPendingApprovals, resolvePendingChange } from '../../lib/api';
import { DiffView } from './DiffView';

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
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
