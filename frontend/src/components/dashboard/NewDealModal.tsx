import { useState } from 'react';

interface NewDealModalProps {
  onClose: () => void;
  onCreate: (data: { name: string; client: string; industries: string[] }) => void;
  creating: boolean;
}

export function NewDealModal({ onClose, onCreate, creating }: NewDealModalProps) {
  const [name, setName] = useState('');
  const [client, setClient] = useState('');
  const [industries, setIndustries] = useState('');

  function submit() {
    if (!name.trim() || !client.trim()) return;
    onCreate({
      name: name.trim(),
      client: client.trim(),
      industries: industries
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-[440px] rounded-md border border-grid bg-panel p-5">
        <div className="mb-4 flex items-center justify-between">
          <div className="text-sm font-bold text-white">New Deal</div>
          <button onClick={onClose} className="cursor-pointer border-none bg-transparent text-base text-gray">
            &times;
          </button>
        </div>
        <div className="flex flex-col gap-3">
          <label className="flex flex-col gap-1">
            <span className="text-[10px] uppercase text-gray">Deal name</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="rounded border border-grid bg-terminal-black px-2.5 py-2 text-xs text-[#e7e7ea] outline-none"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[10px] uppercase text-gray">Client</span>
            <input
              value={client}
              onChange={(e) => setClient(e.target.value)}
              className="rounded border border-grid bg-terminal-black px-2.5 py-2 text-xs text-[#e7e7ea] outline-none"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[10px] uppercase text-gray">Industries (comma-separated)</span>
            <input
              value={industries}
              onChange={(e) => setIndustries(e.target.value)}
              placeholder="Healthcare, Software"
              className="rounded border border-grid bg-terminal-black px-2.5 py-2 text-xs text-[#e7e7ea] outline-none"
            />
          </label>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="cursor-pointer rounded border border-grid bg-transparent px-3.5 py-2 text-xs text-[#e7e7ea]"
          >
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={creating}
            className="cursor-pointer rounded border-none bg-violet px-3.5 py-2 text-xs font-semibold text-white disabled:opacity-50"
          >
            {creating ? 'Creating…' : 'Create deal'}
          </button>
        </div>
      </div>
    </div>
  );
}
