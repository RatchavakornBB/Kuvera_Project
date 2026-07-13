import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { KanbanBoard } from '../components/KanbanBoard';
import { ViewToggle, type DashboardView } from '../components/dashboard/ViewToggle';
import { PipelineFunnelStrip } from '../components/dashboard/PipelineFunnelStrip';
import { DealTable } from '../components/dashboard/DealTable';
import { PipelineListView } from '../components/dashboard/PipelineListView';
import { NeedsAttentionRail } from '../components/dashboard/NeedsAttentionRail';
import { NewDealModal } from '../components/dashboard/NewDealModal';
import { buildStageSegments } from '../lib/dealStage';
import { fetchDeals, createDeal, type ApiDeal } from '../lib/api';
import type { DealCardData } from '../components/DealCard';

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
  const queryClient = useQueryClient();
  const [view, setView] = useState<DashboardView>('board');
  const [stageFilter, setStageFilter] = useState<string | null>(null);
  const [newDealOpen, setNewDealOpen] = useState(false);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['deals'],
    queryFn: fetchDeals,
  });

  const createMutation = useMutation({
    mutationFn: createDeal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deals'] });
      setNewDealOpen(false);
    },
  });

  const allDeals = data ?? [];
  const filteredDeals = stageFilter ? allDeals.filter((d) => d.stage === stageFilter) : allDeals;

  return (
    <div className="p-8">
      <div className="mb-4 flex items-center gap-4">
        <h1 className="text-lg font-semibold text-white">Deals</h1>
        <ViewToggle value={view} onChange={setView} />
        <div className="flex-1" />
        <button
          onClick={() => setNewDealOpen(true)}
          className="cursor-pointer rounded border-none bg-violet px-3.5 py-1.5 text-xs font-semibold text-white"
        >
          + New Deal
        </button>
      </div>

      {isLoading && <div className="text-xs text-gray">Loading deals…</div>}
      {isError && <div className="text-xs text-red">Failed to load deals: {String(error)}</div>}

      {data && (
        <div className="flex flex-col gap-4">
          <PipelineFunnelStrip deals={allDeals} activeStage={stageFilter} onSelectStage={setStageFilter} />

          <div className="flex items-start gap-4">
            <div className="min-w-0 flex-1">
              {view === 'board' && (
                <KanbanBoard
                  deals={filteredDeals.map(toDealCardData)}
                  onOpenDeal={(id) => navigate(`/deals/${id}`)}
                />
              )}
              {view === 'table' && (
                <DealTable deals={filteredDeals} onOpenDeal={(id) => navigate(`/deals/${id}`)} />
              )}
              {view === 'pipeline' && <PipelineListView deals={allDeals} />}
            </div>
            <NeedsAttentionRail deals={allDeals} onOpenDeal={(id) => navigate(`/deals/${id}`)} />
          </div>
        </div>
      )}

      {newDealOpen && (
        <NewDealModal
          onClose={() => setNewDealOpen(false)}
          onCreate={(body) => createMutation.mutate(body)}
          creating={createMutation.isPending}
        />
      )}
    </div>
  );
}
