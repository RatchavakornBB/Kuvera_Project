import { useState } from 'react';
import { AgentsModelsTab } from '../components/admin/AgentsModelsTab';
import { SkillsTab } from '../components/admin/SkillsTab';
import { PendingApprovalsTab } from '../components/admin/PendingApprovalsTab';
import { AuditLogTab } from '../components/admin/AuditLogTab';
import { KnowledgeBaseTab } from '../components/admin/KnowledgeBaseTab';
import { LearningAgentTab } from '../components/admin/LearningAgentTab';

type AdminTab = 'agents' | 'skills' | 'pending' | 'audit' | 'knowledge' | 'learning';

const TABS: { key: AdminTab; label: string }[] = [
  { key: 'agents', label: 'Agents & Models' },
  { key: 'skills', label: 'Skills' },
  { key: 'pending', label: 'Pending Approvals' },
  { key: 'knowledge', label: 'Knowledge Base' },
  { key: 'learning', label: 'Learning Agent' },
  { key: 'audit', label: 'Audit Log' },
];

export function AdminGovernance() {
  const [tab, setTab] = useState<AdminTab>('agents');

  return (
    <div className="flex flex-col gap-4 p-8">
      <div>
        <div className="text-lg font-bold text-white">Admin &amp; Skill Governance</div>
        <div className="mt-1 text-[11px] text-gray">
          Real, DB-backed configuration — approved changes here affect the next real Claude API
          call for that agent. The Knowledge Base tab is real too: closing a deal promotes its
          actual data into pgvector-embedded records that risk_flagger/pricing_advisor retrieve as
          historical precedent, and Industry/Competitor Briefs there use real web search. The
          Learning Agent tab runs real outside-world research and can propose real skill changes
          into the same Pending Approvals queue, where a real (on-demand) eval pass-rate bar —
          real candidate output + real LLM-as-judge grading against a small real test set — helps
          triage a proposal before approving it. Eval cases exist for 3 agents so far
          (pricing_advisor, ic_memo_drafter, risk_flagger); others show "no eval cases defined"
          rather than a fabricated score.
        </div>
      </div>

      <div className="flex gap-0.5 border-b border-grid">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`cursor-pointer border-none border-b-2 bg-transparent px-3.5 py-2 text-xs ${
              tab === t.key ? 'border-violet text-white' : 'border-transparent text-gray'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'agents' && <AgentsModelsTab />}
      {tab === 'skills' && <SkillsTab />}
      {tab === 'pending' && <PendingApprovalsTab />}
      {tab === 'knowledge' && <KnowledgeBaseTab />}
      {tab === 'learning' && <LearningAgentTab />}
      {tab === 'audit' && <AuditLogTab />}
    </div>
  );
}
