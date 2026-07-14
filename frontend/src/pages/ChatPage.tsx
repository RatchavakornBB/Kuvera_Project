import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useOutletContext } from 'react-router-dom';
import {
  fetchDeals,
  fetchDocuments,
  documentDownloadUrl,
  createDeal,
  addLinkSource,
  fetchConversations,
} from '../lib/api';
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
  const [linkInput, setLinkInput] = useState('');
  const queryClient = useQueryClient();

  const { data: deals } = useQuery({ queryKey: ['deals'], queryFn: fetchDeals });
  const activeMode = useMemo(() => MODES.find((m) => m.key === mode)!, [mode]);

  const { data: selectedDealDocuments, isLoading: documentsLoading } = useQuery({
    queryKey: ['documents', { deal_id: selectedDeal?.id }],
    queryFn: () => fetchDocuments({ deal_id: selectedDeal!.id }),
    enabled: !!selectedDeal,
  });

  const { data: conversations } = useQuery({
    queryKey: ['conversations', selectedDeal?.id],
    queryFn: () => fetchConversations(selectedDeal!.id),
    enabled: !!selectedDeal,
  });

  // Real episodic memory, not just an in-page thread: switching to a
  // different deal loads that deal's most recent persisted conversation
  // (or starts a fresh one if it has none yet) instead of carrying over
  // whatever was on screen for the previous deal. lastDealIdRef only
  // advances once we've actually acted on the change (not immediately),
  // so this doesn't skip itself the moment `conversations` finishes
  // loading and re-triggers the effect.
  const lastDealIdRef = useRef<string | undefined>(undefined);
  useEffect(() => {
    if (!selectedDeal) {
      if (lastDealIdRef.current !== undefined) {
        chat.startNewConversation();
        lastDealIdRef.current = undefined;
      }
      return;
    }
    if (selectedDeal.id === lastDealIdRef.current) return;
    if (conversations === undefined) return; // wait for this deal's own query to resolve
    lastDealIdRef.current = selectedDeal.id;
    if (conversations.length > 0) {
      chat.switchConversation(conversations[0].id);
    } else {
      chat.startNewConversation();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDeal?.id, conversations]);

  useEffect(() => {
    if (chat.conversationId) {
      queryClient.invalidateQueries({ queryKey: ['conversations', selectedDeal?.id] });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chat.conversationId]);

  const createMutation = useMutation({
    mutationFn: createDeal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deals'] });
      setNewDealOpen(false);
    },
  });

  const addLinkMutation = useMutation({
    mutationFn: (url: string) => addLinkSource(selectedDeal!.id, url),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', { deal_id: selectedDeal?.id }] });
      setLinkInput('');
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
                        <div className="shrink-0 text-[9px] text-gray">{doc.source_url ? '🔗' : '▪'}</div>
                        {doc.source_url ? (
                          <a
                            href={doc.source_url}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="min-w-0 flex-1 truncate text-[10.5px] text-[#e7e7ea] no-underline hover:text-blue"
                            title={doc.source_url}
                          >
                            {doc.name.replace(/\.txt$/, '')}
                          </a>
                        ) : (
                          <div className="min-w-0 flex-1 truncate text-[10.5px] text-[#e7e7ea]">{doc.name}</div>
                        )}
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

                    <div className="mt-1.5 flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                      <input
                        value={linkInput}
                        onChange={(e) => setLinkInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && linkInput.trim() && addLinkMutation.mutate(linkInput.trim())}
                        placeholder="Paste a URL…"
                        className="min-w-0 flex-1 rounded border border-grid bg-terminal-black px-2 py-1 text-[10px] text-white placeholder:text-gray"
                      />
                      <button
                        onClick={() => linkInput.trim() && addLinkMutation.mutate(linkInput.trim())}
                        disabled={!linkInput.trim() || addLinkMutation.isPending}
                        className="shrink-0 cursor-pointer rounded border-none bg-violet px-2 py-1 text-[10px] font-semibold text-white disabled:opacity-40"
                      >
                        {addLinkMutation.isPending ? '…' : '+ Link'}
                      </button>
                    </div>
                    {addLinkMutation.isError && (
                      <div className="mt-1 text-[9.5px] text-red">{String((addLinkMutation.error as Error)?.message ?? addLinkMutation.error)}</div>
                    )}
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

        {selectedDeal && (
          <div className="flex items-center gap-1 overflow-x-auto border-b border-grid bg-terminal-black px-3 py-1.5">
            {conversations?.map((c) => {
              const isActive = chat.conversationId === c.id;
              return (
                <button
                  key={c.id}
                  onClick={() => chat.switchConversation(c.id)}
                  className="shrink-0 cursor-pointer whitespace-nowrap rounded-sm border-none px-2.5 py-1 text-[10.5px]"
                  style={{
                    background: isActive ? 'var(--color-panel)' : 'transparent',
                    color: isActive ? 'var(--color-violet)' : 'var(--color-gray)',
                  }}
                  title={c.title ?? 'New conversation'}
                >
                  {(c.title ?? 'New conversation').slice(0, 28)}
                </button>
              );
            })}
            <button
              onClick={() => chat.startNewConversation()}
              className="shrink-0 cursor-pointer rounded-sm border-none bg-transparent px-2 py-1 text-[12px] text-violet"
              title="Start a new conversation"
            >
              +
            </button>
          </div>
        )}

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
