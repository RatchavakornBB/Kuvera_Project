import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { StageDiagram } from '../StageDiagram';
import { STAGE_NAMES, buildStageSegments } from '../../lib/dealStage';
import { statusColor } from '../../lib/dealStatus';
import { closeDeal, updateDealStage, type ApiDealDetail } from '../../lib/api';

export function DealDetailHeader({ deal }: { deal: ApiDealDetail }) {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(false);

  const closeMutation = useMutation({
    mutationFn: (outcome: 'won' | 'lost') => closeDeal(deal.id, outcome),
    onSuccess: () => {
      setConfirming(false);
      queryClient.invalidateQueries({ queryKey: ['deal', deal.id] });
      queryClient.invalidateQueries({ queryKey: ['deals'] });
    },
  });

  const stageMutation = useMutation({
    mutationFn: (stage: string) => updateDealStage(deal.id, stage),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deal', deal.id] });
      queryClient.invalidateQueries({ queryKey: ['deals'] });
    },
  });

  return (
    <div className="flex flex-col gap-3 rounded border border-grid bg-panel p-4">
      <div className="flex items-center gap-3.5">
        <div className="text-lg font-bold text-white">{deal.name}</div>
        <div className="text-[11.5px] text-gray">{deal.client}</div>
        {deal.industries.map((ind) => (
          <div key={ind} className="rounded-sm border border-grid px-1.5 py-0.5 text-[10px] text-blue">
            {ind}
          </div>
        ))}
        <div className="flex-1" />

        {deal.status !== 'Closed' && !confirming && (
          <button
            onClick={() => setConfirming(true)}
            className="cursor-pointer rounded border border-grid bg-transparent px-2.5 py-1 text-[10.5px] text-gray"
          >
            Close deal
          </button>
        )}
        {confirming && (
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-gray">Outcome:</span>
            <button
              onClick={() => closeMutation.mutate('won')}
              disabled={closeMutation.isPending}
              className="cursor-pointer rounded border-none bg-green px-2 py-1 text-[10px] font-semibold text-terminal-black disabled:opacity-40"
            >
              Won
            </button>
            <button
              onClick={() => closeMutation.mutate('lost')}
              disabled={closeMutation.isPending}
              className="cursor-pointer rounded border-none bg-red px-2 py-1 text-[10px] font-semibold text-white disabled:opacity-40"
            >
              Lost
            </button>
            <button
              onClick={() => setConfirming(false)}
              className="cursor-pointer border-none bg-transparent px-1 text-[10px] text-gray"
            >
              Cancel
            </button>
          </div>
        )}

        <div className="text-[11px]" style={{ color: statusColor(deal.status) }}>
          {deal.status}
        </div>
        <select
          value={deal.stage}
          disabled={deal.status === 'Closed' || stageMutation.isPending}
          onChange={(e) => stageMutation.mutate(e.target.value)}
          className="cursor-pointer rounded border border-grid bg-transparent px-1.5 py-1 text-[10.5px] text-gray disabled:cursor-not-allowed disabled:opacity-40"
        >
          {STAGE_NAMES.map((name) => (
            <option key={name} value={name} className="bg-panel">
              {name}
            </option>
          ))}
        </select>
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue text-[10px] font-semibold text-terminal-black">
          {deal.owner?.initials ?? '—'}
        </div>
      </div>
      {closeMutation.isSuccess && (
        <div className="text-[10.5px] text-green">
          Deal closed — {closeMutation.data.knowledge_records_created} knowledge records promoted
          to the Knowledge Base.
        </div>
      )}
      {closeMutation.isError && (
        <div className="text-[10.5px] text-red">Failed to close deal: {String(closeMutation.error)}</div>
      )}
      {stageMutation.isError && (
        <div className="text-[10.5px] text-red">Failed to update stage: {String(stageMutation.error)}</div>
      )}
      <StageDiagram segments={buildStageSegments(deal.stage, deal.stage_entered_at)} variant="full" />
    </div>
  );
}
