import { useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadDocument, type ApiDocument } from '../../lib/api';

const STATUS_COLOR: Record<ApiDocument['status'], string> = {
  requested: 'var(--color-amber)',
  received: 'var(--color-green)',
  pending: 'var(--color-amber)',
  under_review: 'var(--color-blue)',
  approved: 'var(--color-green)',
  rejected: 'var(--color-red)',
};

export function DealFileLibrary({ dealId, documents }: { dealId: string; documents: ApiDocument[] }) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument(dealId, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deal', dealId] }),
  });

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <div className="text-xs font-semibold text-white">Deal file library</div>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploadMutation.isPending}
          className="cursor-pointer rounded border-none bg-violet px-3 py-1.5 text-[11px] font-semibold text-white disabled:opacity-50"
        >
          {uploadMutation.isPending ? 'Uploading…' : '+ Add file'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) uploadMutation.mutate(file);
            e.target.value = '';
          }}
        />
      </div>

      <div className="overflow-hidden rounded border border-grid bg-panel">
        {documents.length === 0 && <div className="px-4 py-3 text-[11px] text-gray">No files uploaded yet.</div>}
        {documents.map((doc) => (
          <div key={doc.id} className="flex items-center gap-3 border-b border-grid px-4 py-2.5 last:border-none">
            <div className="h-4 w-4 shrink-0 rounded-sm bg-violet" />
            <div className="min-w-0 flex-1">
              <div className="truncate text-xs font-semibold text-white">{doc.name}</div>
              <div className="truncate text-[10px] text-gray">{doc.summary ?? 'No AI summary yet'}</div>
            </div>
            <div className="shrink-0 text-[9.5px] capitalize" style={{ color: STATUS_COLOR[doc.status] }}>
              {doc.status.replace('_', ' ')}
            </div>
          </div>
        ))}
      </div>
      {uploadMutation.isError && (
        <div className="mt-2 text-[10.5px] text-red">Upload failed: {String(uploadMutation.error)}</div>
      )}
      <div className="mt-1.5 text-[9.5px] text-gray">
        Uploaded files route through the same Storage + Document write path used across the app.
      </div>
    </div>
  );
}
