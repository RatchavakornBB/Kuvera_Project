import type { ApiMeetingNote } from '../../lib/api';

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

export function MeetingNotesFeed({ notes }: { notes: ApiMeetingNote[] }) {
  const sorted = [...notes].sort((a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime());

  return (
    <div className="rounded border border-grid bg-panel p-4">
      <div className="mb-2.5 text-[11.5px] font-semibold text-white">Meeting notes</div>
      {sorted.length === 0 && <div className="text-[11px] text-gray">No meeting notes recorded.</div>}
      <div className="flex flex-col">
        {sorted.map((note) => (
          <div key={note.id} className="flex gap-3 border-b border-grid py-3 last:border-none">
            <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-violet" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between">
                <div className="font-mono text-[10px] text-gray">{formatDateTime(note.occurred_at)}</div>
              </div>
              {note.attendees.length > 0 && (
                <div className="mt-0.5 text-[10px] text-gray">Attendees: {note.attendees.join(', ')}</div>
              )}
              <div className="mt-1 text-[11.5px] leading-relaxed text-[#e7e7ea]">
                {note.summary ?? 'No AI summary yet.'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
