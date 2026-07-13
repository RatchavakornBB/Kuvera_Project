import { useEffect, useRef, useState } from 'react';
import { STAGE_NAMES } from '../lib/dealStage';
import { DealCard, type DealCardData } from './DealCard';

interface KanbanBoardProps {
  deals: DealCardData[];
  onOpenDeal?: (id: string) => void;
}

export function KanbanBoard({ deals, onOpenDeal }: KanbanBoardProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    function updateScrollState() {
      if (!el) return;
      setCanScrollLeft(el.scrollLeft > 4);
      setCanScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 4);
    }

    updateScrollState();
    el.addEventListener('scroll', updateScrollState);
    const resizeObserver = new ResizeObserver(updateScrollState);
    resizeObserver.observe(el);

    return () => {
      el.removeEventListener('scroll', updateScrollState);
      resizeObserver.disconnect();
    };
  }, [deals]);

  return (
    <div className="relative">
      <div ref={scrollRef} className="flex w-full gap-2.5 overflow-x-auto pb-2">
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

      {canScrollLeft && (
        <div className="pointer-events-none absolute bottom-2 left-0 top-0 w-10 bg-gradient-to-r from-terminal-black to-transparent" />
      )}
      {canScrollRight && (
        <div className="pointer-events-none absolute bottom-2 right-0 top-0 w-10 bg-gradient-to-l from-terminal-black to-transparent" />
      )}
    </div>
  );
}
