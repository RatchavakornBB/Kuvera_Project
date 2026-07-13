import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { analyzeDocument, fetchLatestAnalysis, type ApiDealDetail } from '../../lib/api';
import { RiskFlagCards } from './RiskFlagCards';
import { IcMemoPanel } from './IcMemoPanel';
import { PricingSection } from './PricingSection';
import { ContradictionsPanel } from './ContradictionsPanel';
import { DraftingLeadPanel } from './DraftingLeadPanel';

export function AnalysisTab({ deal }: { deal: ApiDealDetail }) {
  const queryClient = useQueryClient();

  const mostRecentDocId = [...deal.documents].sort(
    (a, b) => new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime(),
  )[0]?.id;
  const [selectedDocId, setSelectedDocId] = useState<string | undefined>(mostRecentDocId);

  const { data: analysis, isLoading } = useQuery({
    queryKey: ['analysis', deal.id],
    queryFn: () => fetchLatestAnalysis(deal.id),
  });

  const analyzeMutation = useMutation({
    mutationFn: (documentId: string) => analyzeDocument(deal.id, documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis', deal.id] });
      queryClient.invalidateQueries({ queryKey: ['deal', deal.id] });
    },
  });

  if (deal.documents.length === 0) {
    return (
      <div className="rounded border border-grid bg-panel p-4 text-[11px] text-gray">
        No documents uploaded yet — upload a document in the Documents tab before running analysis.
      </div>
    );
  }

  if (isLoading) {
    return <div className="text-[11px] text-gray">Loading analysis…</div>;
  }

  const displayed = analyzeMutation.data ?? analysis;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 rounded border border-grid bg-panel px-3 py-2">
        <div className="text-[10.5px] text-gray">Source document:</div>
        <select
          value={selectedDocId}
          onChange={(e) => setSelectedDocId(e.target.value)}
          className="flex-1 rounded-sm border border-grid bg-terminal-black px-2 py-1 text-[11px] text-white"
        >
          {deal.documents.map((doc) => (
            <option key={doc.id} value={doc.id}>
              {doc.name}
            </option>
          ))}
        </select>
        <button
          onClick={() => selectedDocId && analyzeMutation.mutate(selectedDocId)}
          disabled={!selectedDocId || analyzeMutation.isPending}
          className="cursor-pointer rounded border-none bg-violet px-3 py-1.5 text-[11px] font-semibold text-white disabled:opacity-50"
        >
          {analyzeMutation.isPending ? 'Analyzing…' : displayed ? 'Regenerate' : 'Generate'}
        </button>
      </div>

      {analyzeMutation.isError && (
        <div className="rounded border-l-2 border-red bg-panel px-3 py-2 text-[11px] text-red">
          Analysis failed: {String(analyzeMutation.error)}
        </div>
      )}

      {!displayed && !analyzeMutation.isPending && (
        <div className="rounded border border-grid bg-panel p-4 text-[11px] text-gray">
          No analysis run yet for this deal — click Generate to run the Analyst Lead against the
          selected document.
        </div>
      )}

      <ContradictionsPanel dealId={deal.id} />

      {displayed && (
        <>
          <RiskFlagCards flags={displayed.risk_flags} />
          <IcMemoPanel
            memo={displayed.ic_memo_draft}
            onRegenerate={() => selectedDocId && analyzeMutation.mutate(selectedDocId)}
            isRegenerating={analyzeMutation.isPending}
          />
          <PricingSection pricingNote={displayed.pricing_note} pricingError={displayed.pricing_error} />
          <DraftingLeadPanel dealId={deal.id} />
        </>
      )}
    </div>
  );
}
