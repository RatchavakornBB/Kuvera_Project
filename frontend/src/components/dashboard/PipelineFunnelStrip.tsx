import { STAGE_NAMES } from '../../lib/dealStage';
import type { ApiDeal } from '../../lib/api';

interface PipelineFunnelStripProps {
  deals: ApiDeal[];
  activeStage: string | null;
  onSelectStage: (stage: string | null) => void;
}

export function PipelineFunnelStrip({ deals, activeStage, onSelectStage }: PipelineFunnelStripProps) {
  return (
    <div className="flex rounded border border-grid bg-panel px-4 py-3.5">
      {STAGE_NAMES.map((stage, i) => {
        const count = deals.filter((d) => d.stage === stage).length;
        const isActive = activeStage === stage;
        return (
          <button
            key={stage}
            onClick={() => onSelectStage(isActive ? null : stage)}
            className={`flex-1 cursor-pointer border-none bg-transparent px-1.5 text-center ${
              i < STAGE_NAMES.length - 1 ? 'border-r border-grid' : ''
            }`}
          >
            <div className={`font-mono text-xl font-semibold ${isActive ? 'text-violet' : 'text-white'}`}>
              {count}
            </div>
            <div className="mt-1 text-[10px] leading-tight text-gray">{stage}</div>
          </button>
        );
      })}
    </div>
  );
}
