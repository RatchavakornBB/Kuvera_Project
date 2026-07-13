export function IcMemoPanel({
  memo,
  onRegenerate,
  isRegenerating,
}: {
  memo: string | null;
  onRegenerate: () => void;
  isRegenerating: boolean;
}) {
  return (
    <div className="rounded border border-grid bg-panel p-4">
      <div className="mb-2.5 flex items-center justify-between">
        <div className="text-[11.5px] font-semibold text-white">IC memo draft</div>
        <button
          onClick={onRegenerate}
          disabled={isRegenerating}
          className="cursor-pointer rounded border border-grid bg-transparent px-2.5 py-1 text-[10.5px] text-blue disabled:opacity-50"
        >
          {isRegenerating ? 'Regenerating…' : 'Regenerate'}
        </button>
      </div>
      {memo ? (
        <div className="whitespace-pre-wrap text-[11.5px] leading-relaxed text-[#e7e7ea]">{memo}</div>
      ) : (
        <div className="text-[11px] text-gray">No IC memo draft yet — run the analysis to generate one.</div>
      )}
      <div className="mt-2.5 text-[9.5px] text-gray">
        AI-drafted — provisional until reviewed by an investment committee member.
      </div>
    </div>
  );
}
