import { useState } from 'react';
import type { AnalyzeResult } from '../../lib/api';

export function PricingSection({
  pricingNote,
  pricingError,
}: {
  pricingNote: string | null;
  pricingError: AnalyzeResult['pricing_error'];
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded border border-grid bg-panel p-4">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full cursor-pointer items-center justify-between border-none bg-transparent p-0 text-left"
      >
        <div className="text-[11.5px] font-semibold text-white">Indicative pricing</div>
        <div className="text-[10px] text-gray">{open ? 'Hide' : 'Show'}</div>
      </button>

      {!pricingNote && !pricingError && (
        <div className="mt-2 rounded-sm border border-grid bg-terminal-black px-2 py-1 text-[9.5px] text-amber inline-block">
          In progress
        </div>
      )}

      {open && (
        <div className="mt-3">
          {pricingError ? (
            <div className="rounded border-l-2 border-red bg-terminal-black px-3 py-2">
              <div className="text-[11px] text-red">
                Pricing advisor failed after {pricingError.attempts} attempt(s) in node "{pricingError.node}".
              </div>
              <div className="mt-1 text-[10px] text-gray">{pricingError.reason}</div>
            </div>
          ) : pricingNote ? (
            <div className="whitespace-pre-wrap text-[11.5px] leading-relaxed text-[#e7e7ea]">{pricingNote}</div>
          ) : (
            <div className="text-[11px] text-gray">Valuation under review — no indicative pricing yet.</div>
          )}
        </div>
      )}
    </div>
  );
}
