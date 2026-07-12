import { StageDiagram, type StageSegment } from './components/StageDiagram';

const STAGE_NAMES = [
  'Lead',
  'NDA',
  'Sourcing & Screening',
  'Valuation & Bidding',
  'Strategy & Preparation',
  'Due Diligence',
  'Negotiation & Closing',
];

function segmentsAtStage(currentIndex: number): StageSegment[] {
  return STAGE_NAMES.map((name, i) => ({
    name,
    status: i < currentIndex ? 'done' : i === currentIndex ? 'current' : 'future',
    days: i <= currentIndex ? (i + 1) * 3 : undefined,
  }));
}

function App() {
  return (
    <div className="min-h-screen bg-terminal-black p-8 text-[#e7e7ea]">
      <h1 className="mb-1 text-lg font-semibold text-white">Stage Diagram — Phase 1 checkpoint</h1>
      <p className="mb-6 text-xs text-gray">Renders correctly for a deal at each of the 7 stages, compact + full variant.</p>

      <div className="flex flex-col gap-5">
        {STAGE_NAMES.map((name, i) => (
          <div key={name} className="rounded border border-grid bg-panel p-4">
            <div className="mb-2 text-xs font-medium text-white">
              Deal at stage: <span className="text-violet">{name}</span>
            </div>
            <div className="mb-3">
              <div className="mb-1 text-[10px] uppercase tracking-wide text-gray">compact</div>
              <StageDiagram segments={segmentsAtStage(i)} variant="compact" />
            </div>
            <div>
              <div className="mb-1 text-[10px] uppercase tracking-wide text-gray">full</div>
              <StageDiagram segments={segmentsAtStage(i)} variant="full" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
