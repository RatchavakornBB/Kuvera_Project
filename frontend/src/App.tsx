import { KanbanBoard } from './components/KanbanBoard';
import { mockDeals } from './data/mockDeals';

function App() {
  return (
    <div className="min-h-screen bg-terminal-black p-8 text-[#e7e7ea]">
      <h1 className="mb-1 text-lg font-semibold text-white">Board view — Phase 1 checkpoint</h1>
      <p className="mb-6 text-xs text-gray">
        Deal card + Kanban column shell, hardcoded demo data — one column per M&amp;A stage.
      </p>

      <KanbanBoard deals={mockDeals} onOpenDeal={(id) => console.log('open deal', id)} />
    </div>
  );
}

export default App;
