import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { fetchDeals, fetchDocuments, documentDownloadUrl, createDeal } from '../lib/api';
import { statusColor } from '../lib/dealStatus';
import { ChatMessage } from '../components/chat/ChatMessage';
import { ChatArtifactCard } from '../components/chat/ChatArtifactCard';
import { ChatComposer } from '../components/chat/ChatComposer';
import { AgentActivityPill } from '../components/chat/AgentActivityPill';
import { NewDealModal } from '../components/dashboard/NewDealModal';
import type { ShellContext } from '../components/layout/AppShell';

// Cosmetic only — the Orchestrator still does the real routing decision on
// every message regardless of which tab is selected (classify_intent in
// agents/nodes/orchestrator.py). These tabs change the composer placeholder
// and accent color, not which agent actually answers.
const MODES = [
  { key: 'concierge', label: 'Concierge', color: 'var(--color-violet)', placeholder: 'Message Concierge...' },
  { key: 'analyst', label: 'Analyst', color: 'var(--color-blue)', placeholder: 'Message Analyst...' },
  { key: 'contracts', label: 'Contracts', color: 'var(--color-green)', placeholder: 'Message Contracts...' },
  { key: 'drafting', label: 'Drafting', color: 'var(--color-amber)', placeholder: 'Message Drafting...' },
] as const;

export function ChatPage() {
  const navigate = useNavigate();
  const { chat, selectedDeal, setSelectedDeal } = useOutletContext<ShellContext>();
  const [mode, setMode] = useState<(typeof MODES)[number]['key']>('concierge');
  const [newDealOpen, setNewDealOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: deals } = useQuery({ queryKey: ['deals'], queryFn: fetchDeals });
  const activeMode = useMemo(() => MODES.find((m) => m.key === mode)!, [mode]);

  const { data: selectedDealDocuments, isLoading: documentsLoading } = useQuery({
    queryKey: ['documents', { deal_id: selectedDeal?.id }],
    queryFn: () => fetchDocuments({ deal_id: selectedDeal!.id }),
    enabled: !!selectedDeal,
  });

  const createMutation = useMutation({
    mutationFn: createDeal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deals'] });
      setNewDealOpen(false);
    },
  });

  return (
    <div className="flex h-full">
      <div className="flex w-[260px] shrink-0 flex-col border-r border-grid bg-panel">
        <div className="flex items-center justify-between border-b border-grid px-3.5 py-3">
          <div className="text-[11.5px] font-semibold text-white">Sources</div>
          <div className="text-[10px] text-gray">{deals?.length ?? 0}</div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {deals?.map((d) => {
            const isSelected = selectedDeal?.id === d.id;
            return (
              <div key={d.id} className="border-b border-grid" style={{ background: isSelected ? 'var(--color-terminal-black)' : undefined }}>
                <div
                  onClick={() => setSelectedDeal(isSelected ? undefined : { id: d.id, name: d.name })}
                  className="flex cursor-pointer items-start gap-2 px-3.5 py-2.5"
                >
                  <div
                    className="mt-0.5 h-3 w-3 shrink-0 rounded-sm"
                    style={{
                      background: isSelected ? statusColor(d.status) : 'transparent',
                      border: `1.5px solid ${statusColor(d.status)}`,
                    }}
                  />
                  <div className="min-w-0">
                    <div className="truncate text-[11.5px] font-semibold text-white">{d.name}</div>
                    <div className="mt-0.5 text-[10px] text-gray">
                      {d.status} · {d.owner?.full_name ?? 'Unassigned'}
                    </div>
                  </div>
                </div>

                {isSelected && (
                  <div className="pb-2 pl-8 pr-3">
                    {documentsLoading && <div className="py-1 text-[10px] text-gray">Loading documents…</div>}
                    {!documentsLoading && (selectedDealDocuments?.length ?? 0) === 0 && (
                      <div className="py-1 text-[10px] text-gray">No documents uploaded for this deal yet.</div>
                    )}
                    {selectedDealDocuments?.map((doc) => (
                      <div key={doc.id} className="flex items-center gap-1.5 py-1">
                        <div className="h-2 w-2 shrink-0 rounded-sm bg-gray" />
                        <div className="min-w-0 flex-1 truncate text-[10.5px] text-[#e7e7ea]">{doc.name}</div>
                        {doc.storage_path && (
                          <a
                            href={documentDownloadUrl(doc.id)}
                            onClick={(e) => e.stopPropagation()}
                            className="shrink-0 text-[10px] text-blue no-underline"
                            title={`Download ${doc.name}`}
                          >
                            ↓
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
        <button
          onClick={() => setNewDealOpen(true)}
          className="cursor-pointer border-none border-t border-grid bg-transparent px-3.5 py-2.5 text-left text-[11px] text-violet"
        >
          + Add source
        </button>
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-4 border-b border-grid px-4 py-2.5">
          {MODES.map((m) => (
            <button
              key={m.key}
              onClick={() => setMode(m.key)}
              className="flex cursor-pointer items-center gap-1.5 border-none bg-transparent p-0 text-[11.5px]"
              style={{ color: mode === m.key ? m.color : 'var(--color-gray)' }}
            >
              <div className="h-1.5 w-1.5 rounded-full" style={{ background: m.color }} />
              {m.label}
            </button>
          ))}
          <div className="flex-1" />
          <div className="text-[10px] text-gray">View agent activity</div>
        </div>

        <div className="flex flex-1 flex-col gap-2.5 overflow-y-auto px-6 py-4">
          {chat.messages.length === 0 && (
            <div className="max-w-[82%] self-start rounded-sm border-l-2 border-violet bg-panel px-3.5 py-3 text-[13px] leading-relaxed text-[#e7e7ea]">
              Hi, I'm your Kuvera Assistant. Ask me about any deal, document, or company in the portfolio.
            </div>
          )}
          {chat.messages.map((m) => (
            <div key={m.id} className="flex flex-col">
              <ChatMessage message={m} />
              {m.artifact && (
                <ChatArtifactCard
                  artifact={m.artifact}
                  onOpen={m.artifact.deal_id ? () => navigate(`/deals/${m.artifact!.deal_id}?tab=analysis`) : undefined}
                />
              )}
            </div>
          ))}
          {chat.busy && <AgentActivityPill label="Kuvera Assistant · thinking…" />}
        </div>

        <div className="px-6 pb-5">
          <ChatComposer
            dealContextLabel={selectedDeal?.name}
            onClearContext={() => setSelectedDeal(undefined)}
            onSend={(text) => chat.send(text, selectedDeal?.id)}
            placeholder={activeMode.placeholder}
          />
        </div>
      </div>

      {newDealOpen && (
        <NewDealModal
          onClose={() => setNewDealOpen(false)}
          onCreate={(body) => createMutation.mutate(body)}
          creating={createMutation.isPending}
        />
      )}
    </div>
  );
}
