import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { fetchKeyDateNotifications } from '../../lib/api';

const DISMISSED_KEY = 'kuvera_dismissed_key_dates';

function loadDismissed(): Set<string> {
  try {
    return new Set(JSON.parse(localStorage.getItem(DISMISSED_KEY) ?? '[]'));
  } catch {
    return new Set();
  }
}

function saveDismissed(ids: Set<string>) {
  localStorage.setItem(DISMISSED_KEY, JSON.stringify([...ids]));
}

export function NotificationBell() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [dismissed, setDismissed] = useState<Set<string>>(() => loadDismissed());

  const { data } = useQuery({
    queryKey: ['key-date-notifications'],
    queryFn: () => fetchKeyDateNotifications(30),
    // On-demand check, not a true server-side cron (system-architecture.md
    // Section 8 / PROCESS/tasks/phase4-004) — client-driven polling is a
    // reasonable stand-in at this dataset's scale, no scheduler infra needed.
    refetchInterval: 5 * 60 * 1000,
  });

  useEffect(() => saveDismissed(dismissed), [dismissed]);

  const items = (data ?? []).filter((n) => !dismissed.has(n.document_id));

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative flex h-7 w-7 cursor-pointer items-center justify-center rounded border border-grid bg-panel"
      >
        <div className="h-3.5 w-3.5 rounded-full border-[1.5px] border-gray" />
        {items.length > 0 && (
          <div className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red px-1 font-mono text-[9px] font-semibold text-white">
            {items.length}
          </div>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-9 z-40 w-[320px] rounded border border-grid bg-panel shadow-lg">
          <div className="border-b border-grid px-3 py-2 text-[10px] font-semibold uppercase tracking-wide text-gray">
            Upcoming key dates
          </div>
          {items.length === 0 && (
            <div className="px-3 py-4 text-center text-[11px] text-gray">No upcoming key dates.</div>
          )}
          {items.map((n) => (
            <div key={n.document_id} className="flex items-start gap-2 border-b border-grid px-3 py-2.5 last:border-none">
              <button
                onClick={() => {
                  navigate(`/deals/${n.deal_id}`);
                  setOpen(false);
                }}
                className="min-w-0 flex-1 cursor-pointer border-none bg-transparent p-0 text-left"
              >
                <div className="truncate text-[11px] text-[#e7e7ea]">{n.document_name}</div>
                <div className="text-[10px] text-gray">{n.deal_name ?? 'Unknown deal'}</div>
                <div className={`font-mono text-[10px] ${n.days_until < 0 ? 'text-red' : 'text-amber'}`}>
                  {n.days_until < 0
                    ? `${Math.abs(n.days_until)}d overdue`
                    : n.days_until === 0
                      ? 'Today'
                      : `${n.days_until}d — ${n.key_date}`}
                </div>
              </button>
              <button
                onClick={() => setDismissed((prev) => new Set(prev).add(n.document_id))}
                className="cursor-pointer border-none bg-transparent p-0 text-xs text-gray"
                title="Dismiss"
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
