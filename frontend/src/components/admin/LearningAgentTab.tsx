import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchLearningDigests, runLearningCycle, type ApiLearningDigest } from '../../lib/api';

const CATEGORY_LABEL: Record<ApiLearningDigest['category'], string> = {
  ma_training_data: 'M&A Training Data',
  prediction_models: 'Prediction Models',
  market_news: 'Market News',
  law_regulation: 'Law & Regulation',
};

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function DigestCard({ digest }: { digest: ApiLearningDigest }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded border border-grid bg-terminal-black">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full cursor-pointer items-center justify-between border-none bg-transparent px-3 py-2.5 text-left"
      >
        <div className="flex min-w-0 items-center gap-2">
          <span className="shrink-0 whitespace-nowrap text-[9.5px] font-semibold uppercase tracking-wide text-violet">
            {CATEGORY_LABEL[digest.category]}
          </span>
          <span className="truncate text-[11px] text-[#e7e7ea]">{digest.topic}</span>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {digest.proposed_change_id && (
            <span className="rounded-sm border border-grid bg-panel px-1.5 py-0.5 text-[9px] text-amber">
              proposed a skill change
            </span>
          )}
          <span className="font-mono text-[9.5px] text-gray">{formatDateTime(digest.created_at)}</span>
        </div>
      </button>
      {open && (
        <div className="border-t border-grid px-3 py-2.5">
          <div className="whitespace-pre-wrap text-[11px] leading-relaxed text-gray">{digest.digest}</div>
          {digest.proposed_change_id && (
            <div className="mt-2 text-[10px] text-amber">
              Proposed a real skill.md addition — review it in the Pending Approvals tab.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function LearningAgentTab() {
  const queryClient = useQueryClient();
  const [category, setCategory] = useState<ApiLearningDigest['category']>('law_regulation');
  const [topic, setTopic] = useState('');

  const { data: digests, isLoading } = useQuery({ queryKey: ['learning-digests'], queryFn: fetchLearningDigests });

  const runMutation = useMutation({
    mutationFn: () => runLearningCycle(category, topic),
    onSuccess: () => {
      setTopic('');
      queryClient.invalidateQueries({ queryKey: ['learning-digests'] });
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] });
    },
  });

  return (
    <div className="flex flex-col gap-3">
      <div className="rounded border border-grid bg-panel p-3">
        <div className="mb-2 text-[10.5px] font-semibold text-white">Run a research cycle</div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as ApiLearningDigest['category'])}
            className="rounded-sm border border-grid bg-terminal-black px-2 py-1.5 text-[11px] text-white"
          >
            {Object.entries(CATEGORY_LABEL).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Specific topic to research…"
            className="min-w-[280px] flex-1 rounded-sm border border-grid bg-terminal-black px-2 py-1.5 text-[11px] text-white placeholder:text-gray"
          />
          <button
            onClick={() => runMutation.mutate()}
            disabled={!topic.trim() || runMutation.isPending}
            className="cursor-pointer rounded border-none bg-violet px-3 py-1.5 text-[11px] font-semibold text-white disabled:opacity-40"
          >
            {runMutation.isPending ? 'Researching…' : 'Run cycle'}
          </button>
        </div>
        <div className="mt-1.5 text-[9.5px] text-gray">
          Real Claude + web_search research, ~15-30s. Only proposes a skill.md change (into the
          same real approval queue the Skills tab uses) when the research surfaces something
          concrete and specific — most cycles propose nothing. On-demand for now, same as the
          Knowledge Base's Brief refresh.
        </div>
        {runMutation.isError && (
          <div className="mt-1.5 text-[10px] text-red">Cycle failed: {String(runMutation.error)}</div>
        )}
      </div>

      {isLoading && <div className="text-[11px] text-gray">Loading…</div>}
      {!isLoading && (!digests || digests.length === 0) && (
        <div className="rounded border border-grid bg-panel p-4 text-center text-[11px] text-gray">
          No research cycles run yet.
        </div>
      )}
      <div className="flex flex-col gap-2">
        {digests?.map((digest) => (
          <DigestCard key={digest.id} digest={digest} />
        ))}
      </div>
    </div>
  );
}
