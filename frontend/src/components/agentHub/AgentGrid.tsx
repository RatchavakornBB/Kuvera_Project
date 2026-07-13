import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchAgentGrid, type ApiAgentGridEntry } from '../../lib/api';

function providerFor(modelId: string): string {
  if (modelId.startsWith('claude-')) return 'anthropic';
  if (modelId.startsWith('gpt-')) return 'openai';
  if (modelId.startsWith('gemini-')) return 'google';
  return 'unknown';
}

const STATUS_COLOR: Record<ApiAgentGridEntry['status'], string> = {
  idle: 'var(--color-gray)',
  active: 'var(--color-violet)',
  error: 'var(--color-red)',
};

function formatRelative(iso: string | null): string {
  if (!iso) return 'never run';
  const ms = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(ms / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function AgentCard({ agent, onOpen }: { agent: ApiAgentGridEntry; onOpen: () => void }) {
  return (
    <button
      onClick={onOpen}
      className="cursor-pointer rounded border border-grid bg-terminal-black p-3 text-left"
    >
      <div className="flex items-center justify-between">
        <div className="text-[11.5px] font-semibold text-white">{agent.agent_name}</div>
        <div
          className="h-[7px] w-[7px] shrink-0 rounded-full"
          style={{
            background: STATUS_COLOR[agent.status],
            animation: agent.status === 'active' ? 'pulse-dot 1s infinite' : undefined,
          }}
        />
      </div>
      <div className="mt-1 font-mono text-[9.5px] text-gray">{agent.model_id}</div>
      <div className="mt-1.5 flex items-center justify-between text-[9.5px]">
        <span style={{ color: STATUS_COLOR[agent.status] }}>{agent.status}</span>
        <span className="text-gray">{formatRelative(agent.last_active)}</span>
      </div>
      {agent.has_skill && (
        <div className="mt-1.5 inline-block rounded-sm border border-grid px-1 py-0.5 text-[8.5px] text-amber">
          custom skill
        </div>
      )}
      {agent.error_reason && (
        <div className="mt-1.5 truncate text-[9px] text-red" title={agent.error_reason}>
          {agent.error_reason}
        </div>
      )}
    </button>
  );
}

export function AgentGrid({ onOpenAgent }: { onOpenAgent: (agentName: string) => void }) {
  const [statusFilter, setStatusFilter] = useState('');
  const [providerFilter, setProviderFilter] = useState('');

  const { data: grid, isLoading } = useQuery({
    queryKey: ['agent-grid'],
    queryFn: fetchAgentGrid,
    refetchInterval: 15000,
  });

  if (isLoading) return <div className="text-[11px] text-gray">Loading…</div>;
  if (!grid) return null;

  const filtered = grid.filter(
    (a) =>
      (!statusFilter || a.status === statusFilter) && (!providerFilter || providerFor(a.model_id) === providerFilter),
  );
  const leads = [...new Set(filtered.map((a) => a.lead))];
  const providers = [...new Set(grid.map((a) => providerFor(a.model_id)))];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded border border-grid bg-panel px-2.5 py-1.5 text-[11px] text-white"
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="idle">Idle</option>
          <option value="error">Error</option>
        </select>
        <select
          value={providerFilter}
          onChange={(e) => setProviderFilter(e.target.value)}
          className="rounded border border-grid bg-panel px-2.5 py-1.5 text-[11px] text-white"
        >
          <option value="">All providers</option>
          {providers.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>

      {leads.length === 0 && (
        <div className="rounded border border-grid bg-panel p-4 text-center text-[11px] text-gray">
          No agents match the current filters.
        </div>
      )}
      {leads.map((lead) => (
        <div key={lead}>
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-gray">{lead}</div>
          <div className="grid grid-cols-4 gap-2.5">
            {filtered
              .filter((a) => a.lead === lead)
              .map((agent) => (
                <AgentCard key={agent.agent_name} agent={agent} onOpen={() => onOpenAgent(agent.agent_name)} />
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}
