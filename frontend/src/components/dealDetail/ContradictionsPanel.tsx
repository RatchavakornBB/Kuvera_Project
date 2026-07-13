import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchContradictions, resolveContradiction, type ApiContradiction } from '../../lib/api';

const STATUS_COLOR: Record<ApiContradiction['status'], string> = {
  unconfirmed: 'var(--color-amber)',
  corroborated: 'var(--color-red)',
  resolved: 'var(--color-green)',
  refuted: 'var(--color-gray)',
};

function ContradictionRow({ dealId, item }: { dealId: string; item: ApiContradiction }) {
  const queryClient = useQueryClient();
  const [note, setNote] = useState('');
  const [showResolve, setShowResolve] = useState(false);

  const resolveMutation = useMutation({
    mutationFn: (resolution: 'resolved' | 'refuted') => resolveContradiction(dealId, item.id, resolution, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contradictions', dealId] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-base'] });
    },
  });

  const open = item.status === 'unconfirmed' || item.status === 'corroborated';

  return (
    <div className="rounded border-l-2 bg-terminal-black px-3 py-2.5" style={{ borderColor: STATUS_COLOR[item.status] }}>
      <div className="flex items-center justify-between">
        <span className="text-[9.5px] font-semibold uppercase tracking-wide" style={{ color: STATUS_COLOR[item.status] }}>
          {item.status} {item.corroboration_count > 1 && `· seen ${item.corroboration_count}×`}
        </span>
        {item.promoted_to_knowledge_base && (
          <span className="text-[9px] text-violet">promoted to Knowledge Base</span>
        )}
      </div>
      <div className="mt-1 text-[11.5px] text-[#e7e7ea]">{item.description}</div>
      {item.source_excerpt && <div className="mt-1 text-[10px] italic text-gray">“{item.source_excerpt}”</div>}
      {item.resolution_note && <div className="mt-1 text-[10px] text-gray">Resolution: {item.resolution_note}</div>}

      {open && (
        <div className="mt-2">
          {!showResolve ? (
            <button
              onClick={() => setShowResolve(true)}
              className="cursor-pointer rounded border border-grid bg-transparent px-2 py-1 text-[10px] text-blue"
            >
              Resolve / refute
            </button>
          ) : (
            <div className="flex flex-col gap-1.5">
              <input
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Resolution note…"
                className="rounded-sm border border-grid bg-panel px-2 py-1 text-[10.5px] text-white placeholder:text-gray"
              />
              <div className="flex gap-1.5">
                <button
                  onClick={() => resolveMutation.mutate('resolved')}
                  disabled={resolveMutation.isPending}
                  className="cursor-pointer rounded border-none bg-green px-2 py-1 text-[10px] font-semibold text-terminal-black disabled:opacity-40"
                >
                  Mark resolved
                </button>
                <button
                  onClick={() => resolveMutation.mutate('refuted')}
                  disabled={resolveMutation.isPending}
                  className="cursor-pointer rounded border border-grid bg-transparent px-2 py-1 text-[10px] text-gray disabled:opacity-40"
                >
                  Refute (false positive)
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ContradictionsPanel({ dealId }: { dealId: string }) {
  const { data: items, isLoading } = useQuery({
    queryKey: ['contradictions', dealId],
    queryFn: () => fetchContradictions(dealId),
  });

  if (isLoading || !items || items.length === 0) return null;

  return (
    <div className="rounded border border-grid bg-panel p-4">
      <div className="mb-2.5 text-[11.5px] font-semibold text-white">Contradictions</div>
      <div className="mb-2 text-[10px] text-gray">
        Tracked separately from ordinary risk flags — status ranks and corroboration count across
        re-analyses, resolved ones promoted into the Knowledge Base.
      </div>
      <div className="flex flex-col gap-2">
        {items.map((item) => (
          <ContradictionRow key={item.id} dealId={dealId} item={item} />
        ))}
      </div>
    </div>
  );
}
