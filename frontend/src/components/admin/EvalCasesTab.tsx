import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createEvalCase,
  deleteEvalCase,
  fetchAgentConfigs,
  fetchBuiltinEvalCaseCounts,
  fetchEvalCases,
  type ApiAgentConfig,
  type ApiEvalCase,
} from '../../lib/api';

// Agents whose eval cases can opt into trajectory grading (agents/evals.py's
// TRAJECTORY_AGENTS) — mirrored here rather than fetched, same known-drift
// tradeoff already accepted for a first cut: keep both lists updated together
// when a new agent gets an agentic loop.
const TRAJECTORY_CAPABLE_AGENTS = ['contracts_lead', 'ic_memo_drafter', 'pricing_advisor'];

function AddEvalCaseForm({ agentName }: { agentName: string }) {
  const queryClient = useQueryClient();
  const [prompt, setPrompt] = useState('');
  const [criteria, setCriteria] = useState('');
  const [expectedToolSequence, setExpectedToolSequence] = useState('');
  const [trajectoryRubric, setTrajectoryRubric] = useState('');
  const trajectoryCapable = TRAJECTORY_CAPABLE_AGENTS.includes(agentName);

  const addMutation = useMutation({
    mutationFn: () =>
      createEvalCase(agentName, prompt, criteria, {
        expectedToolSequence: expectedToolSequence.trim()
          ? expectedToolSequence.split(',').map((s) => s.trim()).filter(Boolean)
          : undefined,
        trajectoryRubric: trajectoryRubric.trim() || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['eval-cases'] });
      setPrompt('');
      setCriteria('');
      setExpectedToolSequence('');
      setTrajectoryRubric('');
    },
  });

  const canSubmit = prompt.trim() && criteria.trim();

  return (
    <div className="rounded border border-grid bg-panel p-4">
      <div className="mb-2 text-[11px] font-semibold text-white">Add Eval Case</div>
      <div className="mb-2 text-[10px] text-gray">
        Write the exact input this agent should receive and what a passing output must do — no
        need to write a tool schema, it's wired automatically for agents that need one. Graded by
        a real LLM-as-judge call the next time an eval runs for {agentName}.
      </div>
      <div className="flex flex-col gap-2">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={4}
          placeholder="Prompt — the exact input to send this agent, including any instructions it would normally get…"
          className="w-full resize-y rounded-sm border border-grid bg-terminal-black px-2.5 py-2 font-mono text-[11px] text-white placeholder:text-gray"
        />
        <textarea
          value={criteria}
          onChange={(e) => setCriteria(e.target.value)}
          rows={2}
          placeholder="Criteria — what a passing output must do, e.g. 'should cite the specific figure X, not decline to answer'…"
          className="w-full resize-y rounded-sm border border-grid bg-terminal-black px-2.5 py-2 font-mono text-[11px] text-white placeholder:text-gray"
        />
        {trajectoryCapable && (
          <details className="rounded-sm border border-grid bg-terminal-black px-2.5 py-2">
            <summary className="cursor-pointer text-[10px] text-gray">
              Trajectory (advanced) — grade the sequence of tool calls, not just the final output
            </summary>
            <div className="mt-2 flex flex-col gap-2">
              <input
                value={expectedToolSequence}
                onChange={(e) => setExpectedToolSequence(e.target.value)}
                placeholder="Expected tool sequence, comma-separated — e.g. search_knowledge, report_contract_analysis"
                className="w-full rounded-sm border border-grid bg-panel px-2.5 py-1.5 font-mono text-[10.5px] text-white placeholder:text-gray"
              />
              <textarea
                value={trajectoryRubric}
                onChange={(e) => setTrajectoryRubric(e.target.value)}
                rows={2}
                placeholder="Trajectory rubric — graded by the same LLM-as-judge, given the full tool-call trajectory plus the final output…"
                className="w-full resize-y rounded-sm border border-grid bg-panel px-2.5 py-1.5 font-mono text-[10.5px] text-white placeholder:text-gray"
              />
              <div className="text-[9.5px] text-gray">
                Set either or both. A circuit-breaker trip or max_iterations truncation during
                grading is reported separately, not averaged into the pass rate.
              </div>
            </div>
          </details>
        )}
        {addMutation.isError && <div className="text-[10px] text-red">{(addMutation.error as Error).message}</div>}
        <button
          onClick={() => addMutation.mutate()}
          disabled={!canSubmit || addMutation.isPending}
          className="cursor-pointer self-start rounded border-none bg-violet px-3.5 py-1.5 text-[11px] font-semibold text-white disabled:opacity-40"
        >
          {addMutation.isPending ? 'Adding…' : 'Add Eval Case'}
        </button>
      </div>
    </div>
  );
}

function EvalCaseList({ agentName, cases }: { agentName: string; cases: ApiEvalCase[] }) {
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: (caseId: string) => deleteEvalCase(caseId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['eval-cases'] }),
  });

  if (cases.length === 0) {
    return <div className="text-[10.5px] text-gray">No admin-added eval cases for {agentName} yet.</div>;
  }

  return (
    <div className="flex flex-col gap-2">
      {cases.map((c) => {
        const isTrajectory = Boolean(c.expected_tool_sequence?.length || c.trajectory_rubric);
        return (
          <div key={c.id} className="rounded-sm border border-grid bg-terminal-black p-3">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1 whitespace-pre-wrap font-mono text-[10.5px] text-[#e7e7ea]">
                {c.prompt}
              </div>
              <div className="flex shrink-0 items-center gap-1.5">
                {isTrajectory && (
                  <span className="rounded-full bg-violet/20 px-1.5 py-0.5 text-[9px] text-violet" title="Trajectory case — grades the sequence of tool calls, not just the final output">
                    trajectory
                  </span>
                )}
                <button
                  onClick={() => deleteMutation.mutate(c.id)}
                  disabled={deleteMutation.isPending}
                  className="cursor-pointer rounded border border-grid bg-transparent px-2 py-0.5 text-[9.5px] text-red disabled:opacity-40"
                >
                  Delete
                </button>
              </div>
            </div>
            <div className="mt-1.5 text-[10px] text-violet">Criteria: {c.criteria}</div>
            {isTrajectory && (
              <div className="mt-1 text-[9.5px] text-gray">
                {c.expected_tool_sequence?.length ? `Expected sequence: ${c.expected_tool_sequence.join(' → ')}` : null}
                {c.expected_tool_sequence?.length && c.trajectory_rubric ? ' · ' : null}
                {c.trajectory_rubric ? `Rubric: ${c.trajectory_rubric}` : null}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function AgentRow({
  agent,
  builtinCount,
  customCount,
  selected,
  onSelect,
}: {
  agent: ApiAgentConfig;
  builtinCount: number;
  customCount: number;
  selected: boolean;
  onSelect: () => void;
}) {
  const total = builtinCount + customCount;
  return (
    <button
      onClick={onSelect}
      className={`flex w-full cursor-pointer items-center justify-between border-none border-b border-grid bg-transparent px-3 py-2.5 text-left text-[11.5px] last:border-none ${
        selected ? 'bg-terminal-black text-white' : 'text-[#e7e7ea]'
      }`}
    >
      <span>{agent.agent_name}</span>
      <span
        className={`ml-1.5 shrink-0 rounded-full px-1.5 py-0.5 text-[9px] ${
          total > 0 ? 'bg-violet/20 text-violet' : 'bg-red/20 text-red'
        }`}
        title={`${builtinCount} built-in + ${customCount} admin-added`}
      >
        {builtinCount}+{customCount}
      </span>
    </button>
  );
}

export function EvalCasesTab() {
  const { data: agents, isLoading: agentsLoading } = useQuery({ queryKey: ['agent-configs'], queryFn: fetchAgentConfigs });
  const { data: builtinCounts, isLoading: countsLoading } = useQuery({
    queryKey: ['eval-cases-builtin-counts'],
    queryFn: fetchBuiltinEvalCaseCounts,
  });
  // Fetched once, unfiltered, and grouped client-side below — avoids firing one
  // request per agent row just to show a count.
  const { data: allCases, isLoading: casesLoading } = useQuery({
    queryKey: ['eval-cases'],
    queryFn: () => fetchEvalCases(),
  });
  const [selected, setSelected] = useState<string | null>(null);

  if (agentsLoading || countsLoading || casesLoading) return <div className="text-[11px] text-gray">Loading…</div>;

  const casesByAgent = new Map<string, ApiEvalCase[]>();
  for (const c of allCases ?? []) {
    casesByAgent.set(c.agent_name, [...(casesByAgent.get(c.agent_name) ?? []), c]);
  }

  return (
    <div className="flex gap-4">
      <div className="w-[240px] shrink-0 overflow-hidden rounded border border-grid bg-panel">
        <div className="border-b border-grid px-3 py-2 text-[10px] uppercase tracking-wide text-gray">
          Agents · built-in + admin-added
        </div>
        {agents?.map((agent) => (
          <AgentRow
            key={agent.id}
            agent={agent}
            builtinCount={builtinCounts?.[agent.agent_name] ?? 0}
            customCount={casesByAgent.get(agent.agent_name)?.length ?? 0}
            selected={selected === agent.agent_name}
            onSelect={() => setSelected(agent.agent_name)}
          />
        ))}
      </div>

      <div className="min-w-0 flex-1 rounded border border-grid bg-panel p-4">
        {!selected ? (
          <div className="text-[11px] text-gray">Select an agent to view or add eval cases.</div>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="text-[11.5px] font-semibold text-white">{selected} — eval cases</div>
            <EvalCaseList agentName={selected} cases={casesByAgent.get(selected) ?? []} />
            <AddEvalCaseForm agentName={selected} />
          </div>
        )}
      </div>
    </div>
  );
}
