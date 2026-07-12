import { StageDiagram, type StageSegment } from './StageDiagram';
import { statusColor, type DealStatus } from '../lib/dealStatus';

export interface DealCardData {
  id: string;
  name: string;
  client: string;
  owner: string; // initials, e.g. "PS"
  riskFlags: number;
  segments: StageSegment[];
  status: DealStatus;
}

interface DealCardProps {
  deal: DealCardData;
  onClick?: (id: string) => void;
}

export function DealCard({ deal, onClick }: DealCardProps) {
  return (
    <div
      onClick={() => onClick?.(deal.id)}
      className="flex cursor-pointer flex-col gap-2 rounded border border-grid bg-panel p-2.5"
    >
      <div className="flex items-start justify-between gap-1.5">
        <div className="text-xs font-semibold text-white">{deal.name}</div>
        {deal.riskFlags > 0 && (
          <div className="shrink-0 rounded-full bg-red px-1.5 py-px font-mono text-[9px] font-semibold text-white">
            {deal.riskFlags}
          </div>
        )}
      </div>

      <div className="text-[10.5px] text-gray">{deal.client}</div>

      <StageDiagram segments={deal.segments} variant="compact" />

      <div className="flex items-center justify-between">
        <div className="flex h-[18px] w-[18px] items-center justify-center rounded-full bg-blue text-[9px] font-semibold text-terminal-black">
          {deal.owner}
        </div>
        <div className="text-[9.5px]" style={{ color: statusColor(deal.status) }}>
          {deal.status}
        </div>
      </div>
    </div>
  );
}
