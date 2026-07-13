import { useQuery } from '@tanstack/react-query';
import { KanbanBoard } from './components/KanbanBoard';
import { ChatPanel } from './components/chat/ChatPanel';
import { buildStageSegments } from './lib/dealStage';
import { fetchDeals, type ApiDeal } from './lib/api';
import type { DealCardData } from './components/DealCard';
import type { ChatMessageData } from './components/chat/ChatMessage';

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

const sampleMessages: ChatMessageData[] = [
  { id: '1', role: 'assistant', text: 'Hi, I’m your Kuvera Assistant. Ask me about any deal, document, or company in the portfolio.' },
  { id: '2', role: 'user', text: 'What’s the status of Deal A?' },
  {
    id: '3',
    role: 'assistant',
    text: 'Deal A is in Due Diligence and On track. The biggest open item is the outstanding FY2025 audited financial statements — I put together a draft IC memo covering the current risks.',
    artifact: { title: 'Deal A — IC memo draft', type: 'Doc' },
  },
];

function App() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['deals'],
    queryFn: fetchDeals,
  });

  return (
    <div className="flex min-h-screen bg-terminal-black text-[#e7e7ea]">
      <div className="flex-1 p-8">
        <h1 className="mb-1 text-lg font-semibold text-white">Deals</h1>
        <p className="mb-6 text-xs text-gray">Board view — live data from the FastAPI /deals endpoint.</p>

        {isLoading && <div className="text-xs text-gray">Loading deals…</div>}
        {isError && <div className="text-xs text-red">Failed to load deals: {String(error)}</div>}
        {data && <KanbanBoard deals={data.map(toDealCardData)} onOpenDeal={(id) => console.log('open deal', id)} />}
      </div>

      <ChatPanel
        messages={sampleMessages}
        traceText="Routed to Analyst Lead → 3.1 → 3.2 → response synthesized"
        dealContextLabel="Deal A"
        onSend={(text) => console.log('send', text)}
      />
    </div>
  );
}

export default App;
