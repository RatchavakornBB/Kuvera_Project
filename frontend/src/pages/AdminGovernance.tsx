import { useState } from 'react';
import { AgentsModelsTab } from '../components/admin/AgentsModelsTab';
import { SkillsTab } from '../components/admin/SkillsTab';
import { PendingApprovalsTab } from '../components/admin/PendingApprovalsTab';
import { AuditLogTab } from '../components/admin/AuditLogTab';
import { KnowledgeBaseTab } from '../components/admin/KnowledgeBaseTab';

type AdminTab = 'agents' | 'skills' | 'pending' | 'audit' | 'knowledge';

const TABS: { key: AdminTab; label: string }[] = [
  { key: 'agents', label: 'Agents & Models' },
  { key: 'skills', label: 'Skills' },
  { key: 'pending', label: 'Pending Approvals' },
  { key: 'knowledge', label: 'Knowledge Base' },
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
          historical precedent. Eval pass-rate scoring isn't built (no eval framework exists yet),
          so that part of the design spec isn't shown here.
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
      {tab === 'audit' && <AuditLogTab />}
    </div>
  );
}
