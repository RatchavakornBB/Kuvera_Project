import { useQuery } from '@tanstack/react-query';
import { fetchSchedulerStatus, fetchScheduledRuns } from '../../lib/api';

const JOB_LABEL: Record<string, string> = {
  key_date_check: 'Key-date check (every 5 min)',
  stalled_deal_check: 'Stalled-deal check (every 5 min)',
  industry_brief_refresh: 'Industry Brief refresh (every 24h)',
  competitor_brief_refresh: 'Competitor Brief refresh (every 24h)',
  company_research_refresh: 'Company Research refresh (every 24h)',
};

function formatDateTime(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function SchedulerStatusPanel() {
  const { data: status } = useQuery({ queryKey: ['scheduler-status'], queryFn: fetchSchedulerStatus, refetchInterval: 30000 });
  const { data: runs } = useQuery({ queryKey: ['scheduled-runs'], queryFn: fetchScheduledRuns, refetchInterval: 30000 });

  return (
    <div className="rounded border border-grid bg-panel p-3">
      <div className="mb-2 text-[10.5px] font-semibold text-white">Real scheduler (server-side, not client polling)</div>
      <div className="mb-2 text-[9.5px] text-gray">
        A real in-process APScheduler (backend/app/scheduler.py) — jobs fire on a real interval
        whether or not anyone has this page open. Key-date checks are cheap (a DB query) so they
        run every 5 minutes; Industry Brief refreshes are real Claude + web_search calls, so those
        run daily to avoid firing costly real API calls too often.
      </div>
      <div className="flex flex-col gap-1.5">
        {status?.jobs.map((job) => (
          <div key={job.id} className="flex items-center justify-between rounded-sm border border-grid bg-terminal-black px-2 py-1.5">
            <span className="text-[10.5px] text-[#e7e7ea]">{JOB_LABEL[job.id] ?? job.id}</span>
            <span className="font-mono text-[9.5px] text-gray">next: {formatDateTime(job.next_run_time)}</span>
          </div>
        ))}
      </div>

      {runs && runs.length > 0 && (
        <div className="mt-2.5">
          <div className="mb-1 text-[9.5px] uppercase tracking-wide text-gray">Recent scheduled runs</div>
          <div className="flex flex-col gap-1">
            {runs.slice(0, 5).map((run) => (
              <div key={run.id} className="flex items-center justify-between text-[10px]">
                <span className={run.status === 'success' ? 'text-green' : 'text-red'}>
                  {JOB_LABEL[run.job_name] ?? run.job_name}
                  {run.detail ? ` — ${run.detail}` : ''}
                </span>
                <span className="font-mono text-gray">{formatDateTime(run.started_at)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
