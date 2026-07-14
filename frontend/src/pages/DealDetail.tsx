import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, useOutletContext, useParams, useSearchParams } from 'react-router-dom';
import { DealDetailHeader } from '../components/dealDetail/DealDetailHeader';
import { DealDetailTabs, type DealTab } from '../components/dealDetail/DealDetailTabs';
import { OverviewTab } from '../components/dealDetail/OverviewTab';
import { RequiredDocumentsChecklist } from '../components/dealDetail/RequiredDocumentsChecklist';
import { DealFileLibrary } from '../components/dealDetail/DealFileLibrary';
import { AnalysisTab } from '../components/dealDetail/AnalysisTab';
import { TaskList } from '../components/dealDetail/TaskList';
import { MeetingNotesFeed } from '../components/dealDetail/MeetingNotesFeed';
import { AskAboutDealPanel } from '../components/dealDetail/AskAboutDealPanel';
import { fetchDeal } from '../lib/api';
import type { ShellContext } from '../components/layout/AppShell';

export function DealDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { askAboutDeal } = useOutletContext<ShellContext>();
  const [searchParams] = useSearchParams();
  const initialTab = searchParams.get('tab');
  const validTabs: DealTab[] = ['overview', 'documents', 'analysis', 'tasks'];
  const [tab, setTab] = useState<DealTab>(
    validTabs.includes(initialTab as DealTab) ? (initialTab as DealTab) : 'overview',
  );

  const { data: deal, isLoading, isError } = useQuery({
    queryKey: ['deal', id],
    queryFn: () => fetchDeal(id!),
    enabled: !!id,
  });

  if (isLoading) return <div className="p-8 text-xs text-gray">Loading deal…</div>;
  if (isError || !deal) return <div className="p-8 text-xs text-red">Failed to load deal.</div>;

  return (
    <div className="flex flex-col gap-4 p-8">
      <button onClick={() => navigate('/')} className="cursor-pointer self-start border-none bg-transparent text-[11px] text-gray">
        &larr; All deals
      </button>

      <DealDetailHeader deal={deal} />
      <DealDetailTabs value={tab} onChange={setTab} />

      <div className="flex items-start gap-4">
        <div className="min-w-0 flex-1">
          {tab === 'overview' && <OverviewTab deal={deal} />}
          {tab === 'documents' && (
            <div className="flex flex-col gap-4">
              <RequiredDocumentsChecklist items={deal.dd_items} />
              <DealFileLibrary dealId={deal.id} documents={deal.documents} />
            </div>
          )}
          {tab === 'analysis' && <AnalysisTab deal={deal} />}
          {tab === 'tasks' && (
            <div className="flex flex-col gap-4">
              <TaskList dealId={deal.id} tasks={deal.tasks} />
              <MeetingNotesFeed notes={deal.meeting_notes} />
            </div>
          )}
        </div>
        <AskAboutDealPanel dealName={deal.name} onAsk={() => askAboutDeal(deal.id, deal.name)} />
      </div>
    </div>
  );
}
