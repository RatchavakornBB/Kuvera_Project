import { STAGE_NAMES } from '../../lib/dealStage';
import type { ApiDeal } from '../../lib/api';

export function PipelineListView({ deals }: { deals: ApiDeal[] }) {
  const maxCount = Math.max(1, ...STAGE_NAMES.map((s) => deals.filter((d) => d.stage === s).length));

  return (
    <div className="flex flex-col gap-2">
      {STAGE_NAMES.map((stage) => {
        const count = deals.filter((d) => d.stage === stage).length;
        return (
          <div key={stage} className="flex items-center gap-4 rounded border border-grid bg-panel px-4 py-3">
            <div className="w-[180px] text-xs text-[#e7e7ea]">{stage}</div>
            <div className="h-2 flex-1 overflow-hidden rounded bg-terminal-black">
              <div className="h-full bg-violet" style={{ width: `${(count / maxCount) * 100}%` }} />
            </div>
            <div className="w-6 text-right font-mono text-sm font-semibold text-white">{count}</div>
          </div>
        );
      })}
    </div>
  );
}
