import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  draftDeck,
  draftEmail,
  draftMemo,
  draftSourceCitedSummary,
  documentDownloadUrl,
} from '../../lib/api';

export function DraftingLeadPanel({ dealId }: { dealId: string }) {
  const queryClient = useQueryClient();
  const [emailText, setEmailText] = useState<string | null>(null);
  const [summaryText, setSummaryText] = useState<string | null>(null);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['deal', dealId] });

  const memoMutation = useMutation({ mutationFn: () => draftMemo(dealId), onSuccess: invalidate });
  const deckMutation = useMutation({ mutationFn: () => draftDeck(dealId), onSuccess: invalidate });
  const emailMutation = useMutation({
    mutationFn: () => draftEmail(dealId),
    onSuccess: (res) => setEmailText(res.email),
  });
  const summaryMutation = useMutation({
    mutationFn: () => draftSourceCitedSummary(dealId),
    onSuccess: (res) => setSummaryText(res.summary),
  });

  return (
    <div className="rounded border border-grid bg-panel p-4">
      <div className="mb-1 text-[11.5px] font-semibold text-white">Drafting Lead</div>
      <div className="mb-2.5 text-[10px] text-gray">
        Real generated files (real .docx/.pptx, uploaded to Storage and added to the file library
        below) — not placeholders. Requires a stored analysis to draft from.
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => memoMutation.mutate()}
          disabled={memoMutation.isPending}
          className="cursor-pointer rounded border border-grid bg-transparent px-2.5 py-1.5 text-[10.5px] text-blue disabled:opacity-40"
        >
          {memoMutation.isPending ? 'Drafting…' : 'Draft IC Memo (.docx)'}
        </button>
        <button
          onClick={() => deckMutation.mutate()}
          disabled={deckMutation.isPending}
          className="cursor-pointer rounded border border-grid bg-transparent px-2.5 py-1.5 text-[10.5px] text-blue disabled:opacity-40"
        >
          {deckMutation.isPending ? 'Drafting…' : 'Draft IC Deck (.pptx)'}
        </button>
        <button
          onClick={() => emailMutation.mutate()}
          disabled={emailMutation.isPending}
          className="cursor-pointer rounded border border-grid bg-transparent px-2.5 py-1.5 text-[10.5px] text-blue disabled:opacity-40"
        >
          {emailMutation.isPending ? 'Drafting…' : 'Draft cover email'}
        </button>
        <button
          onClick={() => summaryMutation.mutate()}
          disabled={summaryMutation.isPending}
          className="cursor-pointer rounded border border-grid bg-transparent px-2.5 py-1.5 text-[10.5px] text-blue disabled:opacity-40"
        >
          {summaryMutation.isPending ? 'Drafting…' : 'Source-cited summary'}
        </button>
      </div>

      {memoMutation.isSuccess && (
        <div className="mt-2 text-[10.5px] text-green">
          Memo drafted —{' '}
          <a href={documentDownloadUrl(memoMutation.data.id)} className="text-blue underline">
            download {memoMutation.data.name}
          </a>{' '}
          (also in the file library below)
        </div>
      )}
      {deckMutation.isSuccess && (
        <div className="mt-2 text-[10.5px] text-green">
          Deck drafted —{' '}
          <a href={documentDownloadUrl(deckMutation.data.id)} className="text-blue underline">
            download {deckMutation.data.name}
          </a>{' '}
          (also in the file library below)
        </div>
      )}
      {(memoMutation.isError || deckMutation.isError || emailMutation.isError || summaryMutation.isError) && (
        <div className="mt-2 text-[10.5px] text-red">
          Drafting failed — a stored analysis is required first.
        </div>
      )}

      {emailText && (
        <div className="mt-3 rounded-sm border border-grid bg-terminal-black p-2.5">
          <div className="mb-1 text-[9.5px] uppercase tracking-wide text-gray">Cover email draft</div>
          <div className="whitespace-pre-wrap text-[11px] leading-relaxed text-[#e7e7ea]">{emailText}</div>
        </div>
      )}
      {summaryText && (
        <div className="mt-3 rounded-sm border border-grid bg-terminal-black p-2.5">
          <div className="mb-1 text-[9.5px] uppercase tracking-wide text-gray">Source-cited summary</div>
          <div className="whitespace-pre-wrap text-[11px] leading-relaxed text-[#e7e7ea]">{summaryText}</div>
        </div>
      )}
    </div>
  );
}
