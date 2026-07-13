import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createTask, updateTask, type ApiTask } from '../../lib/api';

function formatDue(iso: string | null): string {
  if (!iso) return 'No due date';
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

export function TaskList({ dealId, tasks }: { dealId: string; tasks: ApiTask[] }) {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState('');

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['deal', dealId] });

  const toggleMutation = useMutation({
    mutationFn: (task: ApiTask) => updateTask(dealId, task.id, { done: !task.done }),
    onSuccess: invalidate,
  });

  const addMutation = useMutation({
    mutationFn: (text: string) => createTask(dealId, { text }),
    onSuccess: () => {
      setDraft('');
      invalidate();
    },
  });

  const pending = tasks.filter((t) => !t.done);
  const done = tasks.filter((t) => t.done);

  return (
    <div className="rounded border border-grid bg-panel p-4">
      <div className="mb-2.5 text-[11.5px] font-semibold text-white">Tasks</div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (draft.trim()) addMutation.mutate(draft.trim());
        }}
        className="mb-3 flex gap-2"
      >
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Add a task…"
          className="flex-1 rounded-sm border border-grid bg-terminal-black px-2.5 py-1.5 text-[11px] text-white placeholder:text-gray"
        />
        <button
          type="submit"
          disabled={!draft.trim() || addMutation.isPending}
          className="cursor-pointer rounded border-none bg-violet px-3 py-1.5 text-[11px] font-semibold text-white disabled:opacity-50"
        >
          Add
        </button>
      </form>

      {tasks.length === 0 && <div className="text-[11px] text-gray">No tasks yet.</div>}

      <div className="flex flex-col">
        {pending.map((task) => (
          <label
            key={task.id}
            className="flex cursor-pointer items-center gap-2.5 border-b border-grid py-2 last:border-none"
          >
            <input
              type="checkbox"
              checked={task.done}
              onChange={() => toggleMutation.mutate(task)}
              className="h-3.5 w-3.5 shrink-0 cursor-pointer accent-violet"
            />
            <div className="min-w-0 flex-1 text-xs text-[#e7e7ea]">{task.text}</div>
            <div className="shrink-0 font-mono text-[10px] text-gray">{formatDue(task.due_date)}</div>
          </label>
        ))}
        {done.length > 0 && (
          <div className="mt-2 border-t border-grid pt-2">
            <div className="mb-1 text-[9.5px] uppercase tracking-wide text-gray">Done ({done.length})</div>
            {done.map((task) => (
              <label key={task.id} className="flex cursor-pointer items-center gap-2.5 py-1.5">
                <input
                  type="checkbox"
                  checked={task.done}
                  onChange={() => toggleMutation.mutate(task)}
                  className="h-3.5 w-3.5 shrink-0 cursor-pointer accent-violet"
                />
                <div className="min-w-0 flex-1 text-xs text-gray line-through">{task.text}</div>
              </label>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
