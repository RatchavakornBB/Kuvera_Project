import { StageDiagram } from '../StageDiagram';
import { buildStageSegments } from '../../lib/dealStage';
import { statusColor } from '../../lib/dealStatus';
import type { ApiDealDetail } from '../../lib/api';

export function DealDetailHeader({ deal }: { deal: ApiDealDetail }) {
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
        <div className="text-[11px]" style={{ color: statusColor(deal.status) }}>
          {deal.status}
        </div>
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue text-[10px] font-semibold text-terminal-black">
          {deal.owner?.initials ?? '—'}
        </div>
      </div>
      <StageDiagram segments={buildStageSegments(deal.stage, deal.stage_entered_at)} variant="full" />
    </div>
  );
}
