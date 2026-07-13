export function AskAboutDealPanel({ dealName, onAsk }: { dealName: string; onAsk: () => void }) {
  return (
    <div className="w-[220px] shrink-0 rounded border border-grid bg-panel p-3.5">
      <div className="mb-2 text-xs font-semibold text-white">Ask about this deal</div>
      <div className="mb-2.5 text-[10.5px] text-gray">
        Opens the Orchestrator, primed with {dealName}&rsquo;s context.
      </div>
      <button
        onClick={onAsk}
        className="w-full cursor-pointer rounded border-none bg-violet py-2 text-[11px] font-semibold text-white"
      >
        Ask Kuvera Assistant
      </button>
    </div>
  );
}
