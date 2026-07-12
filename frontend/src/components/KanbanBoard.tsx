import { STAGE_NAMES } from '../lib/dealStage';
import { DealCard, type DealCardData } from './DealCard';

interface KanbanBoardProps {
  deals: DealCardData[];
  onOpenDeal?: (id: string) => void;
}

export function KanbanBoard({ deals, onOpenDeal }: KanbanBoardProps) {
  return (
    <div className="flex gap-2.5 overflow-x-auto pb-2">
      {STAGE_NAMES.map((stageName, stageIndex) => {
        const dealsInColumn = deals.filter(
          (d) => d.segments.findIndex((s) => s.status === 'current') === stageIndex,
        );
        return (
          <div key={stageName} className="w-[200px] min-w-[200px] shrink-0">
            <div className="mb-2 border-b border-grid px-0.5 pb-2 pt-1 text-[10.5px] uppercase tracking-wide text-gray">
              {stageName}
            </div>
            <div className="flex flex-col gap-2">
              {dealsInColumn.map((deal) => (
                <DealCard key={deal.id} deal={deal} onClick={onOpenDeal} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
