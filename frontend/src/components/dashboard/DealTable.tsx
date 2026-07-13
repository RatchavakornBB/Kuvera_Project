import { StageDiagram } from '../StageDiagram';
import { buildStageSegments } from '../../lib/dealStage';
import { statusColor } from '../../lib/dealStatus';
import { relativeTime } from '../../lib/relativeTime';
import type { ApiDeal } from '../../lib/api';

export function DealTable({ deals, onOpenDeal }: { deals: ApiDeal[]; onOpenDeal: (id: string) => void }) {
  return (
    <div className="overflow-hidden rounded border border-grid bg-panel">
      <div className="grid grid-cols-[1.4fr_1fr_0.9fr_1.3fr_0.6fr_0.8fr_0.9fr_0.8fr] gap-3 border-b border-grid px-3 py-2 text-[10px] uppercase tracking-wide text-gray">
        <div>Deal</div>
        <div>Client</div>
        <div>Industry</div>
        <div>Stage</div>
        <div>Owner</div>
        <div>Docs pending</div>
        <div>Status</div>
        <div>Last activity</div>
      </div>
      {deals.map((d) => (
        <div
          key={d.id}
          onClick={() => onOpenDeal(d.id)}
          className="grid cursor-pointer grid-cols-[1.4fr_1fr_0.9fr_1.3fr_0.6fr_0.8fr_0.9fr_0.8fr] items-center gap-3 border-b border-grid px-3 py-2.5 text-[11.5px]"
        >
          <div className="font-semibold text-white">{d.name}</div>
          <div className="text-gray">{d.client}</div>
          <div className="text-gray">{d.industries[0] ?? '—'}</div>
          <div>
            <StageDiagram segments={buildStageSegments(d.stage, d.stage_entered_at)} variant="compact" />
          </div>
          <div className="flex h-[18px] w-[18px] items-center justify-center rounded-full bg-blue font-mono text-[9px] font-semibold text-terminal-black">
            {d.owner?.initials ?? '—'}
          </div>
          <div className="font-mono">{d.docs_pending}</div>
          <div style={{ color: statusColor(d.status) }}>{d.status}</div>
          <div className="font-mono text-[10.5px] text-gray">{relativeTime(d.updated_at)}</div>
        </div>
      ))}
    </div>
  );
}
