import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { KanbanBoard } from './components/KanbanBoard';
import { ChatPanel } from './components/chat/ChatPanel';
import { buildStageSegments } from './lib/dealStage';
import { fetchDeals, type ApiDeal } from './lib/api';
import { useChatSocket } from './lib/useChatSocket';
import type { DealCardData } from './components/DealCard';

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

const DEAL_A_ID = 'd0000000-0000-0000-0000-00000000000a';

function App() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['deals'],
    queryFn: fetchDeals,
  });

  const { messages, busy, send } = useChatSocket();
  const [dealContextId, setDealContextId] = useState<string | undefined>(DEAL_A_ID);
  const dealContextLabel = dealContextId ? data?.find((d) => d.id === dealContextId)?.name : undefined;

  return (
    <div className="flex min-h-screen bg-terminal-black text-[#e7e7ea]">
      <div className="flex-1 p-8">
        <h1 className="mb-1 text-lg font-semibold text-white">Deals</h1>
        <p className="mb-6 text-xs text-gray">Board view — live data from the FastAPI /deals endpoint.</p>

        {isLoading && <div className="text-xs text-gray">Loading deals…</div>}
        {isError && <div className="text-xs text-red">Failed to load deals: {String(error)}</div>}
        {data && (
          <KanbanBoard deals={data.map(toDealCardData)} onOpenDeal={(id) => setDealContextId(id)} />
        )}
      </div>

      <ChatPanel
        messages={messages}
        agentBusyLabel={busy ? 'Kuvera Assistant · thinking…' : undefined}
        dealContextLabel={dealContextLabel}
        onClearContext={() => setDealContextId(undefined)}
        onSend={(text) => send(text, dealContextId)}
      />
    </div>
  );
}

export default App;
