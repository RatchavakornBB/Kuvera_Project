import { useQuery } from '@tanstack/react-query';
import { fetchAuditLog } from '../../lib/api';

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

export function AuditLogTab() {
  const { data: entries, isLoading } = useQuery({ queryKey: ['audit-log'], queryFn: fetchAuditLog });

  if (isLoading) return <div className="text-[11px] text-gray">Loading…</div>;

  return (
    <div className="overflow-hidden rounded border border-grid bg-panel">
      <div className="grid grid-cols-[1.1fr_1fr_2fr_0.7fr_1.2fr] gap-3 border-b border-grid px-4 py-2 text-[10px] uppercase tracking-wide text-gray">
        <div>Agent</div>
        <div>Field</div>
        <div>New value</div>
        <div>Action</div>
        <div>When</div>
      </div>
      {(!entries || entries.length === 0) && (
        <div className="px-4 py-6 text-center text-[11px] text-gray">
          No approved or rejected changes yet.
        </div>
      )}
      {entries?.map((entry) => (
        <div
          key={entry.id}
          className="grid grid-cols-[1.1fr_1fr_2fr_0.7fr_1.2fr] items-center gap-3 border-b border-grid px-4 py-2.5 text-[11px] last:border-none"
        >
          <div className="font-semibold text-white">{entry.agent_name}</div>
          <div className="text-gray">{entry.change_type}</div>
          <div className="truncate text-[#e7e7ea]" title={entry.new_value}>
            {entry.new_value || '(empty)'}
          </div>
          <div className={entry.action === 'approved' ? 'text-green' : 'text-red'}>{entry.action}</div>
          <div className="font-mono text-[10px] text-gray">{formatDateTime(entry.created_at)}</div>
        </div>
      ))}
    </div>
  );
}
