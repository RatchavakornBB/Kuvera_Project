import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchAgentConfigs, proposeAgentChange, type ApiAgentConfig } from '../../lib/api';

const KNOWN_MODELS = ['claude-sonnet-5', 'claude-opus-4-8', 'claude-haiku-4-5-20251001', 'claude-fable-5'];

function AgentRow({ agent }: { agent: ApiAgentConfig }) {
  const queryClient = useQueryClient();
  const [modelId, setModelId] = useState(agent.model_id);

  const proposeMutation = useMutation({
    mutationFn: () => proposeAgentChange(agent.agent_name, 'model_id', modelId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pending-approvals'] }),
  });

  const dirty = modelId !== agent.model_id;

  return (
    <div className="flex items-center gap-3 border-b border-grid px-4 py-2.5 last:border-none">
      <div className="w-[180px] shrink-0 text-xs font-semibold text-white">{agent.agent_name}</div>
      <select
        value={modelId}
        onChange={(e) => setModelId(e.target.value)}
        className="flex-1 rounded-sm border border-grid bg-terminal-black px-2 py-1.5 text-[11px] text-white"
      >
        {[...new Set([agent.model_id, ...KNOWN_MODELS])].map((m) => (
          <option key={m} value={m}>
            {m}
          </option>
        ))}
      </select>
      <button
        onClick={() => proposeMutation.mutate()}
        disabled={!dirty || proposeMutation.isPending}
        className="cursor-pointer rounded border border-grid bg-transparent px-2.5 py-1.5 text-[10.5px] text-blue disabled:opacity-40"
      >
        {proposeMutation.isPending ? 'Proposing…' : proposeMutation.isSuccess && !dirty ? 'Proposed ✓' : 'Propose change'}
      </button>
    </div>
  );
}

export function AgentsModelsTab() {
  const { data: agents, isLoading } = useQuery({ queryKey: ['agent-configs'], queryFn: fetchAgentConfigs });

  return (
    <div className="rounded border border-grid bg-panel">
      <div className="border-b border-grid px-4 py-2.5 text-[10px] uppercase tracking-wide text-gray">
        Only claude-* models are actually wired to a provider right now — proposing a gpt-*/gemini-*
        model_id will genuinely fail at call time (NotImplementedError), not silently no-op.
      </div>
      {isLoading && <div className="px-4 py-3 text-[11px] text-gray">Loading…</div>}
      {agents?.map((agent) => (
        <AgentRow key={agent.id} agent={agent} />
      ))}
    </div>
  );
}
