import { statusColor } from '../../lib/dealStatus';
import { relativeTime } from '../../lib/relativeTime';
import type { ApiDeal } from '../../lib/api';

export function NeedsAttentionRail({ deals, onOpenDeal }: { deals: ApiDeal[]; onOpenDeal: (id: string) => void }) {
  const flagged = deals.filter((d) => d.status === 'Needs attention' || d.status === 'Stalled');

  return (
    <div className="w-[240px] shrink-0 rounded border border-grid bg-panel p-3.5">
      <div className="mb-2.5 text-[11.5px] font-semibold text-white">Needs attention</div>
      <div className="flex flex-col gap-2">
        {flagged.length === 0 && <div className="text-[11px] text-gray">Nothing needs attention right now.</div>}
        {flagged.map((d) => (
          <div
            key={d.id}
            onClick={() => onOpenDeal(d.id)}
            className="cursor-pointer rounded-sm bg-terminal-black px-2 py-1.5"
            style={{ borderLeft: `2px solid ${statusColor(d.status)}` }}
          >
            <div className="text-[11.5px] font-semibold text-white">{d.name}</div>
            <div className="mt-0.5 text-[10px]" style={{ color: statusColor(d.status) }}>
              {d.status} · {relativeTime(d.updated_at)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
