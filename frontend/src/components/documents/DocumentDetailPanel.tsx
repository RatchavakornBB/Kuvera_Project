import { useNavigate } from 'react-router-dom';
import type { ApiDocumentWithDeal } from '../../lib/api';

export function DocumentDetailPanel({
  document,
  onClose,
}: {
  document: ApiDocumentWithDeal;
  onClose: () => void;
}) {
  const navigate = useNavigate();

  return (
    <div className="w-[320px] shrink-0 rounded border border-grid bg-panel p-4">
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="min-w-0 text-xs font-semibold text-white">{document.name}</div>
        <button onClick={onClose} className="cursor-pointer border-none bg-transparent text-sm text-gray">
          &times;
        </button>
      </div>

      {document.deal && (
        <button
          onClick={() => navigate(`/deals/${document.deal!.id}`)}
          className="mb-3 cursor-pointer border-none bg-transparent p-0 text-[10.5px] text-blue"
        >
          {document.deal.name} &rarr;
        </button>
      )}

      <div className="mb-3">
        <div className="mb-1 text-[9.5px] uppercase tracking-wide text-gray">AI summary</div>
        <div className="whitespace-pre-wrap text-[11px] leading-relaxed text-[#e7e7ea]">
          {document.summary ?? 'No AI summary yet.'}
        </div>
      </div>

      <div className="mb-3">
        <div className="mb-1 text-[9.5px] uppercase tracking-wide text-gray">Key clauses</div>
        {document.clauses.length === 0 ? (
          <div className="text-[11px] text-gray">No clauses extracted for this document.</div>
        ) : (
          <div className="flex flex-col gap-2">
            {document.clauses.map((clause, i) => (
              <div key={i} className="rounded-sm border border-grid bg-terminal-black px-2.5 py-2">
                <div className="text-[9.5px] font-semibold uppercase tracking-wide text-violet">{clause.label}</div>
                <div className="mt-0.5 text-[10.5px] text-[#e7e7ea]">{clause.text}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <div className="mb-1 text-[9.5px] uppercase tracking-wide text-gray">Status</div>
        <div className="text-[11px] capitalize text-[#e7e7ea]">{document.status.replace('_', ' ')}</div>
      </div>
    </div>
  );
}
