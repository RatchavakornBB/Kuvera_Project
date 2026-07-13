import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchAgentConfigs, proposeAgentChange, type ApiAgentConfig } from '../../lib/api';
import { DiffView } from './DiffView';

export function SkillsTab() {
  const queryClient = useQueryClient();
  const { data: agents, isLoading } = useQuery({ queryKey: ['agent-configs'], queryFn: fetchAgentConfigs });
  const [selected, setSelected] = useState<ApiAgentConfig | null>(null);
  const [draft, setDraft] = useState('');

  function select(agent: ApiAgentConfig) {
    setSelected(agent);
    setDraft(agent.skill_content);
  }

  const proposeMutation = useMutation({
    mutationFn: () => proposeAgentChange(selected!.agent_name, 'skill_content', draft),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] });
    },
  });

  if (isLoading) return <div className="text-[11px] text-gray">Loading…</div>;

  return (
    <div className="flex gap-4">
      <div className="w-[220px] shrink-0 overflow-hidden rounded border border-grid bg-panel">
        <div className="border-b border-grid px-3 py-2 text-[10px] uppercase tracking-wide text-gray">
          Agents
        </div>
        {agents?.map((agent) => (
          <button
            key={agent.id}
            onClick={() => select(agent)}
            className={`block w-full cursor-pointer border-none border-b border-grid bg-transparent px-3 py-2.5 text-left text-[11.5px] last:border-none ${
              selected?.id === agent.id ? 'bg-terminal-black text-white' : 'text-[#e7e7ea]'
            }`}
          >
            {agent.agent_name}
            {agent.skill_content && <span className="ml-1.5 text-[9px] text-violet">●</span>}
          </button>
        ))}
      </div>

      <div className="min-w-0 flex-1 rounded border border-grid bg-panel p-4">
        {!selected ? (
          <div className="text-[11px] text-gray">Select an agent to view or edit its skill.</div>
        ) : (
          <div className="flex flex-col gap-3">
            <div className="text-[11.5px] font-semibold text-white">{selected.agent_name} — skill.md</div>
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={6}
              placeholder="No skill instructions set — this agent runs on its base prompt only."
              className="w-full resize-y rounded-sm border border-grid bg-terminal-black px-2.5 py-2 font-mono text-[11px] text-white placeholder:text-gray"
            />

            <div>
              <div className="mb-1 text-[9.5px] uppercase tracking-wide text-gray">Diff vs. current</div>
              <DiffView oldText={selected.skill_content} newText={draft} />
            </div>

            <button
              onClick={() => proposeMutation.mutate()}
              disabled={draft === selected.skill_content || proposeMutation.isPending}
              className="cursor-pointer self-start rounded border-none bg-violet px-3.5 py-1.5 text-[11px] font-semibold text-white disabled:opacity-40"
            >
              {proposeMutation.isPending ? 'Proposing…' : 'Propose change'}
            </button>
            {proposeMutation.isSuccess && (
              <div className="text-[10.5px] text-green">
                Proposed — check the Pending Approvals tab to approve it.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
