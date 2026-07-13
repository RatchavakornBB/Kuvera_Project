import type { ApiDealDetail } from '../../lib/api';

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

export function OverviewTab({ deal }: { deal: ApiDealDetail }) {
  const keyDates = deal.documents.filter((d) => d.key_date);

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded border border-grid bg-panel p-4">
        <div className="mb-4 text-[11.5px] font-semibold text-white">Deal timeline</div>
        {deal.milestones.length === 0 ? (
          <div className="text-[11px] text-gray">No timeline yet — milestones will populate as this deal progresses.</div>
        ) : (
          <div className="flex justify-between">
            {deal.milestones.map((m) => (
              <div key={m.id} className="flex w-[120px] flex-col items-center text-center">
                <div
                  className={`h-3 w-3 rounded-full border-2 ${
                    m.occurred_at ? 'border-green bg-green' : 'border-grid bg-panel'
                  }`}
                />
                <div className={`mt-2 text-[10.5px] leading-tight ${m.occurred_at ? 'text-[#e7e7ea]' : 'text-gray'}`}>
                  {m.label}
                </div>
                <div className="mt-1 font-mono text-[9.5px] text-gray">{formatDate(m.occurred_at)}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-4">
        <div className="flex-1 rounded border border-grid bg-panel p-4">
          <div className="mb-2.5 text-[11.5px] font-semibold text-white">External contacts</div>
          {deal.contacts.length === 0 && <div className="text-[11px] text-gray">No contacts recorded.</div>}
          {deal.contacts.map((c) => (
            <div key={c.id} className="border-b border-grid py-2 last:border-none">
              <div className="text-xs font-semibold text-white">{c.name}</div>
              <div className="text-[10.5px] text-gray">{c.role ?? 'Role unknown'}</div>
              <div className="mt-0.5 font-mono text-[10px] text-gray">
                Last contacted {formatDate(c.last_contacted_at)}
              </div>
            </div>
          ))}
        </div>

        <div className="flex-1 rounded border border-grid bg-panel p-4">
          <div className="mb-2.5 text-[11.5px] font-semibold text-white">Key dates</div>
          {keyDates.length === 0 && <div className="text-[11px] text-gray">No upcoming key dates.</div>}
          {keyDates.map((d) => (
            <div key={d.id} className="flex justify-between border-b border-grid py-1.5 last:border-none">
              <div className="text-[11.5px] text-[#e7e7ea]">{d.name}</div>
              <div className="font-mono text-[10.5px] text-amber">{formatDate(d.key_date)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
