import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { fetchDeals, fetchKeyDateNotifications } from '../lib/api';
import { statusColor } from '../lib/dealStatus';
import { relativeTime } from '../lib/relativeTime';

export function Today() {
  const navigate = useNavigate();

  const { data: deals, isLoading: dealsLoading } = useQuery({ queryKey: ['deals'], queryFn: fetchDeals });
  const { data: keyDates, isLoading: datesLoading } = useQuery({
    queryKey: ['key-date-notifications'],
    queryFn: () => fetchKeyDateNotifications(30),
  });

  const flagged = (deals ?? []).filter((d) => d.status === 'Needs attention' || d.status === 'Stalled');

  return (
    <div className="flex flex-col gap-4 p-8">
      <div className="text-lg font-bold text-white">Today</div>

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded border border-grid bg-panel p-4">
          <div className="mb-3 text-[11.5px] font-semibold text-white">Deals needing attention</div>
          {dealsLoading && <div className="text-[11px] text-gray">Loading…</div>}
          {!dealsLoading && flagged.length === 0 && (
            <div className="text-[11px] text-gray">Nothing needs attention right now.</div>
          )}
          <div className="flex flex-col gap-2">
            {flagged.map((d) => (
              <div
                key={d.id}
                onClick={() => navigate(`/deals/${d.id}`)}
                className="cursor-pointer rounded-sm bg-terminal-black px-3 py-2"
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

        <div className="rounded border border-grid bg-panel p-4">
          <div className="mb-3 text-[11.5px] font-semibold text-white">Upcoming key dates (30 days)</div>
          {datesLoading && <div className="text-[11px] text-gray">Loading…</div>}
          {!datesLoading && (keyDates?.length ?? 0) === 0 && (
            <div className="text-[11px] text-gray">No upcoming key dates.</div>
          )}
          <div className="flex flex-col gap-2">
            {keyDates?.map((n) => (
              <div
                key={n.document_id}
                onClick={() => navigate(`/deals/${n.deal_id}`)}
                className="cursor-pointer rounded-sm bg-terminal-black px-3 py-2"
              >
                <div className="text-[11.5px] text-[#e7e7ea]">{n.document_name}</div>
                <div className="mt-0.5 text-[10px] text-gray">{n.deal_name ?? 'Unknown deal'}</div>
                <div className={`font-mono text-[10px] ${n.days_until < 0 ? 'text-red' : 'text-amber'}`}>
                  {n.days_until < 0
                    ? `${Math.abs(n.days_until)}d overdue`
                    : n.days_until === 0
                      ? 'Today'
                      : `${n.days_until}d — ${n.key_date}`}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
