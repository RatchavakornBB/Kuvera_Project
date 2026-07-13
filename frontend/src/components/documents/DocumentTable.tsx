import type { ApiDocumentWithDeal } from '../../lib/api';

const STATUS_COLOR: Record<ApiDocumentWithDeal['status'], string> = {
  requested: 'var(--color-amber)',
  received: 'var(--color-green)',
  pending: 'var(--color-amber)',
  under_review: 'var(--color-blue)',
  approved: 'var(--color-green)',
  rejected: 'var(--color-red)',
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function daysUntil(iso: string): number {
  return Math.ceil((new Date(iso).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
}

export function DocumentTable({
  documents,
  onOpenDocument,
}: {
  documents: ApiDocumentWithDeal[];
  onOpenDocument: (doc: ApiDocumentWithDeal) => void;
}) {
  return (
    <div className="overflow-hidden rounded border border-grid bg-panel">
      <div className="grid grid-cols-[1.6fr_1fr_0.8fr_0.9fr_1.8fr_0.9fr_0.9fr] gap-3 border-b border-grid px-3 py-2 text-[10px] uppercase tracking-wide text-gray">
        <div>Name</div>
        <div>Deal</div>
        <div>Type</div>
        <div>Uploaded</div>
        <div>AI summary</div>
        <div>Status</div>
        <div>Key date</div>
      </div>
      {documents.length === 0 && (
        <div className="px-4 py-6 text-center text-[11px] text-gray">No documents match the current filters.</div>
      )}
      {documents.map((doc) => {
        const days = doc.key_date ? daysUntil(doc.key_date) : null;
        const nearDue = days !== null && days <= 30;
        return (
          <div
            key={doc.id}
            onClick={() => onOpenDocument(doc)}
            className="grid cursor-pointer grid-cols-[1.6fr_1fr_0.8fr_0.9fr_1.8fr_0.9fr_0.9fr] items-center gap-3 border-b border-grid px-3 py-2.5 text-[11.5px] last:border-none hover:bg-terminal-black"
          >
            <div className="truncate font-semibold text-white">{doc.name}</div>
            <div className="truncate text-gray">{doc.deal?.name ?? '—'}</div>
            <div className="text-gray">{doc.type}</div>
            <div className="font-mono text-[10.5px] text-gray">{formatDate(doc.uploaded_at)}</div>
            <div className="truncate text-[10.5px] text-gray">{doc.summary ?? 'No AI summary yet'}</div>
            <div className="capitalize" style={{ color: STATUS_COLOR[doc.status] }}>
              {doc.status.replace('_', ' ')}
            </div>
            <div className="font-mono text-[10.5px]">
              {doc.key_date ? (
                <span className={nearDue ? (days! < 0 ? 'text-red' : 'text-amber') : 'text-gray'}>
                  {formatDate(doc.key_date)}
                  {nearDue && (
                    <span className="ml-1 rounded-sm border border-grid bg-terminal-black px-1 py-0.5 text-[9px]">
                      {days! < 0 ? `${Math.abs(days!)}d overdue` : `${days}d`}
                    </span>
                  )}
                </span>
              ) : (
                <span className="text-gray">—</span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
