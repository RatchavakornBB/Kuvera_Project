import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { addSkillInstruction, createAgent, fetchAgentConfigs, proposeAgentChange, type ApiAgentConfig } from '../../lib/api';
import { formatSkillSection, parseSkillSections } from '../../lib/skillSections';
import { DiffView } from './DiffView';

const KNOWN_MODELS = ['claude-sonnet-5', 'claude-opus-4-8', 'claude-haiku-4-5-20251001', 'claude-fable-5'];

function AddSkillForm({ agents }: { agents: ApiAgentConfig[] }) {
  const queryClient = useQueryClient();
  const [agentName, setAgentName] = useState(agents[0]?.agent_name ?? '');
  const [skillName, setSkillName] = useState('');
  const [instruction, setInstruction] = useState('');
  const [lastAdded, setLastAdded] = useState<{ name: string; agentName: string } | null>(null);

  const addMutation = useMutation({
    mutationFn: () => addSkillInstruction(agentName, formatSkillSection(skillName, instruction)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] });
      setLastAdded({ name: skillName, agentName });
      setSkillName('');
      setInstruction('');
    },
  });

  const canSubmit = agentName && skillName.trim() && instruction.trim();

  return (
    <div className="rounded border border-grid bg-panel p-4">
      <div className="mb-2 text-[11px] font-semibold text-white">Add Skill</div>
      <div className="mb-2 text-[10px] text-gray">
        Adds one named skill to whichever agent you pick below — appended alongside its existing skills, never
        overwriting them.
      </div>
      <div className="flex flex-col gap-2">
        <select
          value={agentName}
          onChange={(e) => setAgentName(e.target.value)}
          className="w-full rounded-sm border border-grid bg-terminal-black px-2 py-1.5 text-[11px] text-white"
        >
          {agents.map((agent) => (
            <option key={agent.id} value={agent.agent_name}>
              {agent.agent_name}
            </option>
          ))}
        </select>
        <input
          value={skillName}
          onChange={(e) => setSkillName(e.target.value)}
          placeholder="Skill name, e.g. 'Thailand PDPA check'"
          className="w-full rounded-sm border border-grid bg-terminal-black px-2.5 py-1.5 text-[11px] text-white placeholder:text-gray"
        />
        <textarea
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          rows={2}
          placeholder="What this skill instructs the agent to do…"
          className="w-full resize-y rounded-sm border border-grid bg-terminal-black px-2.5 py-2 font-mono text-[11px] text-white placeholder:text-gray"
        />
        {addMutation.isError && <div className="text-[10px] text-red">{(addMutation.error as Error).message}</div>}
        <button
          onClick={() => addMutation.mutate()}
          disabled={!canSubmit || addMutation.isPending}
          className="cursor-pointer self-start rounded border-none bg-violet px-3.5 py-1.5 text-[11px] font-semibold text-white disabled:opacity-40"
        >
          {addMutation.isPending ? 'Adding…' : 'Add Skill'}
        </button>
        {addMutation.isSuccess && lastAdded && (
          <div className="text-[10.5px] text-green">
            Proposed "{lastAdded.name}" for {lastAdded.agentName} — check the Pending Approvals tab to approve it.
          </div>
        )}
      </div>
    </div>
  );
}

function NewAgentForm({ onCreated }: { onCreated: (agent: ApiAgentConfig) => void }) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [agentName, setAgentName] = useState('');
  const [modelId, setModelId] = useState(KNOWN_MODELS[0]);
  const [skillName, setSkillName] = useState('');
  const [skillContent, setSkillContent] = useState('');

  const createMutation = useMutation({
    mutationFn: () =>
      createAgent(
        agentName.trim(),
        modelId,
        skillName.trim() && skillContent.trim() ? formatSkillSection(skillName, skillContent) : '',
      ),
    onSuccess: (agent) => {
      queryClient.invalidateQueries({ queryKey: ['agent-configs'] });
      setOpen(false);
      setAgentName('');
      setSkillName('');
      setSkillContent('');
      onCreated(agent);
    },
  });

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="w-full cursor-pointer border-none border-b border-grid bg-transparent px-3 py-2.5 text-left text-[11.5px] text-blue"
      >
        + New agent
      </button>
    );
  }

  return (
    <div className="flex flex-col gap-2 border-b border-grid px-3 py-2.5">
      <input
        value={agentName}
        onChange={(e) => setAgentName(e.target.value)}
        placeholder="agent_name (snake_case)"
        className="w-full rounded-sm border border-grid bg-terminal-black px-2 py-1.5 font-mono text-[10.5px] text-white placeholder:text-gray"
      />
      <select
        value={modelId}
        onChange={(e) => setModelId(e.target.value)}
        className="w-full rounded-sm border border-grid bg-terminal-black px-2 py-1.5 text-[10.5px] text-white"
      >
        {KNOWN_MODELS.map((m) => (
          <option key={m} value={m}>
            {m}
          </option>
        ))}
      </select>
      <input
        value={skillName}
        onChange={(e) => setSkillName(e.target.value)}
        placeholder="Initial skill name (optional)"
        className="w-full rounded-sm border border-grid bg-terminal-black px-2 py-1.5 text-[10.5px] text-white placeholder:text-gray"
      />
      <textarea
        value={skillContent}
        onChange={(e) => setSkillContent(e.target.value)}
        rows={3}
        placeholder="Initial skill instructions (optional)"
        className="w-full resize-y rounded-sm border border-grid bg-terminal-black px-2 py-1.5 font-mono text-[10.5px] text-white placeholder:text-gray"
      />
      {createMutation.isError && (
        <div className="text-[10px] text-red">{(createMutation.error as Error).message}</div>
      )}
      <div className="flex gap-2">
        <button
          onClick={() => createMutation.mutate()}
          disabled={!agentName.trim() || createMutation.isPending}
          className="cursor-pointer rounded border-none bg-violet px-2.5 py-1 text-[10.5px] font-semibold text-white disabled:opacity-40"
        >
          {createMutation.isPending ? 'Creating…' : 'Create'}
        </button>
        <button
          onClick={() => setOpen(false)}
          className="cursor-pointer rounded border border-grid bg-transparent px-2.5 py-1 text-[10.5px] text-gray"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

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
    <div className="flex flex-col gap-4">
      {agents && agents.length > 0 && <AddSkillForm agents={agents} />}

      <div className="flex gap-4">
        <div className="w-[220px] shrink-0 overflow-hidden rounded border border-grid bg-panel">
          <div className="border-b border-grid px-3 py-2 text-[10px] uppercase tracking-wide text-gray">
            Agents
          </div>
          {agents?.map((agent) => {
            const skillCount = parseSkillSections(agent.skill_content).length;
            return (
              <button
                key={agent.id}
                onClick={() => select(agent)}
                className={`flex w-full cursor-pointer items-center justify-between border-none border-b border-grid bg-transparent px-3 py-2.5 text-left text-[11.5px] last:border-none ${
                  selected?.id === agent.id ? 'bg-terminal-black text-white' : 'text-[#e7e7ea]'
                }`}
              >
                <span>{agent.agent_name}</span>
                {skillCount > 0 && (
                  <span
                    className="ml-1.5 shrink-0 rounded-full bg-violet/20 px-1.5 py-0.5 text-[9px] text-violet"
                    title={`${skillCount} skill${skillCount === 1 ? '' : 's'}`}
                  >
                    {skillCount}
                  </span>
                )}
              </button>
            );
          })}
          <NewAgentForm onCreated={select} />
        </div>

        <div className="min-w-0 flex-1 rounded border border-grid bg-panel p-4">
          {!selected ? (
            <div className="text-[11px] text-gray">Select an agent to view or edit its skill.</div>
          ) : (
            <div className="flex flex-col gap-3">
              <div className="text-[11.5px] font-semibold text-white">{selected.agent_name} — skill.md</div>

              {(() => {
                const sections = parseSkillSections(selected.skill_content);
                if (sections.length === 0) return null;
                return (
                  <div>
                    <div className="mb-1 text-[9.5px] uppercase tracking-wide text-gray">
                      {sections.length} skill{sections.length === 1 ? '' : 's'} on this agent
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {sections.map((section, i) => (
                        <span
                          key={i}
                          title={section.content}
                          className="rounded-sm border border-grid bg-terminal-black px-2 py-1 text-[10px] text-[#e7e7ea]"
                        >
                          {section.name}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })()}

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
    </div>
  );
}
