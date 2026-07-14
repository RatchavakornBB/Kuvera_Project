import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchDeals, fetchDocuments, type ApiDocumentWithDeal } from '../lib/api';
import { DocumentTable } from '../components/documents/DocumentTable';
import { DocumentDetailPanel } from '../components/documents/DocumentDetailPanel';
import { UploadDocumentModal } from '../components/documents/UploadDocumentModal';
import { KeyDatesStrip } from '../components/documents/KeyDatesStrip';

const DOC_TYPES = ['PDF', 'Financial', 'Document', 'Image', 'Contract', 'Link'];
const DOC_STATUSES = ['requested', 'received', 'pending', 'under_review', 'approved', 'rejected'];
const SEARCH_DEBOUNCE_MS = 400;

export function DocumentsContracts() {
  const [qInput, setQInput] = useState('');
  const [q, setQ] = useState('');
  const [dealFilter, setDealFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selected, setSelected] = useState<ApiDocumentWithDeal | null>(null);
  const [showUpload, setShowUpload] = useState(false);

  // The search box now drives a real Voyage AI embedding call per query
  // (pgvector semantic search), not a free local substring filter — debounce
  // so typing doesn't fire one paid API call per keystroke.
  useEffect(() => {
    const timer = setTimeout(() => setQ(qInput), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [qInput]);

  const { data: deals } = useQuery({ queryKey: ['deals'], queryFn: fetchDeals });

  const filters = { deal_id: dealFilter, type: typeFilter, status: statusFilter, q };
  const { data: documents, isLoading, isError } = useQuery({
    queryKey: ['documents', filters],
    queryFn: () => fetchDocuments(filters),
  });

  return (
    <div className="flex flex-col gap-4 p-8">
      <div className="flex items-center justify-between">
        <div className="text-lg font-bold text-white">Documents &amp; Contracts</div>
        <button
          onClick={() => setShowUpload(true)}
          className="cursor-pointer rounded border-none bg-violet px-3.5 py-2 text-xs font-semibold text-white"
        >
          + Upload
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <input
          value={qInput}
          onChange={(e) => setQInput(e.target.value)}
          placeholder="Semantic search — try a concept, not just a filename…"
          className="min-w-[220px] flex-1 rounded border border-grid bg-panel px-3 py-2 text-[11.5px] text-white placeholder:text-gray"
        />
        <select
          value={dealFilter}
          onChange={(e) => setDealFilter(e.target.value)}
          className="rounded border border-grid bg-panel px-2.5 py-2 text-[11.5px] text-white"
        >
          <option value="">All deals</option>
          {deals?.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="rounded border border-grid bg-panel px-2.5 py-2 text-[11.5px] text-white"
        >
          <option value="">All types</option>
          {DOC_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded border border-grid bg-panel px-2.5 py-2 text-[11.5px] text-white capitalize"
        >
          <option value="">All statuses</option>
          {DOC_STATUSES.map((s) => (
            <option key={s} value={s} className="capitalize">
              {s.replace('_', ' ')}
            </option>
          ))}
        </select>
      </div>

      {documents && documents.length > 0 && <KeyDatesStrip documents={documents} />}

      {isLoading && <div className="text-[11px] text-gray">Loading documents…</div>}
      {isError && <div className="text-[11px] text-red">Failed to load documents.</div>}

      {documents && (
        <div className="flex items-start gap-4">
          <div className="min-w-0 flex-1">
            <DocumentTable documents={documents} onOpenDocument={setSelected} />
          </div>
          {selected && <DocumentDetailPanel document={selected} onClose={() => setSelected(null)} />}
        </div>
      )}

      {showUpload && <UploadDocumentModal onClose={() => setShowUpload(false)} />}
    </div>
  );
}
