import { useQuery } from '@tanstack/react-query';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { KanbanBoard } from '../components/KanbanBoard';
import { buildStageSegments } from '../lib/dealStage';
import { fetchDeals, type ApiDeal } from '../lib/api';
import type { DealCardData } from '../components/DealCard';
import type { ShellContext } from '../components/layout/AppShell';

function toDealCardData(deal: ApiDeal): DealCardData {
  return {
    id: deal.id,
    name: deal.name,
    client: deal.client,
    owner: deal.owner?.initials ?? '—',
    riskFlags: deal.risk_flags,
    status: deal.status,
    segments: buildStageSegments(deal.stage, deal.stage_entered_at),
  };
}

export function Dashboard() {
  const navigate = useNavigate();
  useOutletContext<ShellContext>();
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['deals'],
    queryFn: fetchDeals,
  });

  return (
    <div className="p-8">
      <h1 className="mb-1 text-lg font-semibold text-white">Deals</h1>
      <p className="mb-6 text-xs text-gray">Board view — live data from the FastAPI /deals endpoint.</p>

      {isLoading && <div className="text-xs text-gray">Loading deals…</div>}
      {isError && <div className="text-xs text-red">Failed to load deals: {String(error)}</div>}
      {data && (
        <KanbanBoard deals={data.map(toDealCardData)} onOpenDeal={(id) => navigate(`/deals/${id}`)} />
      )}
    </div>
  );
}
