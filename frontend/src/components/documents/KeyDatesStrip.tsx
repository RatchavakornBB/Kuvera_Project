import type { ApiDocumentWithDeal } from '../../lib/api';

function daysUntil(iso: string): number {
  const ms = new Date(iso).getTime() - Date.now();
  return Math.ceil(ms / (1000 * 60 * 60 * 24));
}

export function KeyDatesStrip({ documents }: { documents: ApiDocumentWithDeal[] }) {
  const upcoming = documents
    .filter((d) => d.key_date && daysUntil(d.key_date) <= 30)
    .sort((a, b) => new Date(a.key_date!).getTime() - new Date(b.key_date!).getTime());

  if (upcoming.length === 0) return null;

  return (
    <div className="rounded border border-amber/40 bg-panel px-4 py-2.5">
      <div className="mb-1.5 text-[9.5px] font-semibold uppercase tracking-wide text-amber">
        Upcoming key dates
      </div>
      <div className="flex flex-wrap gap-2">
        {upcoming.map((d) => {
          const days = daysUntil(d.key_date!);
          return (
            <div
              key={d.id}
              className="flex items-center gap-2 rounded-sm border border-grid bg-terminal-black px-2.5 py-1 text-[10.5px]"
            >
              <span className="text-[#e7e7ea]">{d.name}</span>
              <span className="text-gray">· {d.deal?.name ?? 'Unknown deal'}</span>
              <span className={`font-mono ${days < 0 ? 'text-red' : 'text-amber'}`}>
                {days < 0 ? `${Math.abs(days)}d overdue` : days === 0 ? 'Today' : `${days}d`}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
