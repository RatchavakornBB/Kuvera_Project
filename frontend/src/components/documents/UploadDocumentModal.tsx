import { useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchDeals, uploadDocument } from '../../lib/api';

export function UploadDocumentModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const { data: deals } = useQuery({ queryKey: ['deals'], queryFn: fetchDeals });
  const [dealId, setDealId] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument(dealId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      onClose();
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-[420px] rounded-md border border-grid bg-panel p-5">
        <div className="mb-4 flex items-center justify-between">
          <div className="text-sm font-bold text-white">Upload document</div>
          <button onClick={onClose} className="cursor-pointer border-none bg-transparent text-base text-gray">
            &times;
          </button>
        </div>

        <label className="flex flex-col gap-1">
          <span className="text-[10px] uppercase text-gray">Deal</span>
          <select
            value={dealId}
            onChange={(e) => setDealId(e.target.value)}
            className="rounded border border-grid bg-terminal-black px-2.5 py-2 text-xs text-[#e7e7ea] outline-none"
          >
            <option value="">Select a deal…</option>
            {deals?.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </label>

        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={!dealId || uploadMutation.isPending}
          className="mt-4 w-full cursor-pointer rounded border border-dashed border-grid bg-terminal-black px-3 py-6 text-[11px] text-gray disabled:opacity-50"
        >
          {uploadMutation.isPending ? 'Uploading…' : 'Click to choose a file'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file && dealId) uploadMutation.mutate(file);
            e.target.value = '';
          }}
        />

        {uploadMutation.isError && (
          <div className="mt-2 text-[10.5px] text-red">Upload failed: {String(uploadMutation.error)}</div>
        )}

        <div className="mt-5 flex justify-end">
          <button
            onClick={onClose}
            className="cursor-pointer rounded border border-grid bg-transparent px-3.5 py-2 text-xs text-[#e7e7ea]"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
