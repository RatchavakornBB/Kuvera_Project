import { useMemo, useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  createPhase,
  createTask,
  deletePhase,
  updatePhase,
  updateTask,
  type ApiPhase,
  type ApiTask,
} from '../../lib/api';
import {
  PX_PER_DAY,
  addDays,
  buildTicks,
  dayDiff,
  parseDate,
  toISO,
  todayUTC,
  type Zoom,
} from '../../lib/gantt';

const PHASE_ROW_H = 36;
const TASK_ROW_H = 30;
const HEADER_H = 44;
const LEFT_W = 240;

type Override = { start_date: string; end_date: string };

/** A task whose dates already have any live-drag override merged in. */
type EffTask = ApiTask & { _start: Date | null; _end: Date | null };

interface DragState {
  taskId: string;
  mode: 'move' | 'resize-start' | 'resize-end';
  startX: number;
  origStart: Date;
  origEnd: Date;
}

export function ProjectPlanTab({ dealId, tasks, phases }: { dealId: string; tasks: ApiTask[]; phases: ApiPhase[] }) {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['deal', dealId] });

  const [zoom, setZoom] = useState<Zoom>('day');
  const [overrides, setOverrides] = useState<Record<string, Override>>({});
  const [addingPhase, setAddingPhase] = useState(false);
  const [phaseDraft, setPhaseDraft] = useState('');
  const [taskDraftFor, setTaskDraftFor] = useState<string | null>(null);
  const [taskDraft, setTaskDraft] = useState('');
  const dragRef = useRef<DragState | null>(null);

  const px = PX_PER_DAY[zoom];

  const taskMutation = useMutation({
    mutationFn: (v: { id: string; body: Parameters<typeof updateTask>[2] }) => updateTask(dealId, v.id, v.body),
    onSuccess: (_d, v) => {
      setOverrides((o) => {
        const next = { ...o };
        delete next[v.id];
        return next;
      });
      invalidate();
    },
  });
  const addTaskMutation = useMutation({
    mutationFn: (v: Parameters<typeof createTask>[1]) => createTask(dealId, v),
    onSuccess: () => {
      setTaskDraft('');
      setTaskDraftFor(null);
      invalidate();
    },
  });
  const phaseMutation = useMutation({
    mutationFn: (v: { id: string; body: Parameters<typeof updatePhase>[2] }) => updatePhase(dealId, v.id, v.body),
    onSuccess: invalidate,
  });
  const addPhaseMutation = useMutation({
    mutationFn: (name: string) => createPhase(dealId, { name }),
    onSuccess: () => {
      setPhaseDraft('');
      setAddingPhase(false);
      invalidate();
    },
  });
  const delPhaseMutation = useMutation({
    mutationFn: (id: string) => deletePhase(dealId, id),
    onSuccess: invalidate,
  });

  // Effective dates = stored dates with any live override applied.
  const effTasks = useMemo<EffTask[]>(() => {
    return tasks.map((t) => {
      const ov = overrides[t.id];
      const start = ov?.start_date ?? t.start_date;
      const end = ov?.end_date ?? t.end_date;
      return { ...t, _start: start ? parseDate(start) : null, _end: end ? parseDate(end) : null };
    });
  }, [tasks, overrides]);

  // Timeline range spans all scheduled dates (padded), min 34 days wide.
  const { rangeStart, totalDays } = useMemo(() => {
    const dates: Date[] = [];
    for (const t of effTasks) {
      if (t._start) dates.push(t._start);
      if (t._end) dates.push(t._end);
    }
    const today = todayUTC();
    let min = dates.length ? new Date(Math.min(...dates.map((d) => d.getTime()))) : addDays(today, -3);
    let max = dates.length ? new Date(Math.max(...dates.map((d) => d.getTime()))) : addDays(today, 30);
    min = addDays(min, -3);
    max = addDays(max, 7);
    let total = dayDiff(min, max) + 1;
    if (total < 34) {
      max = addDays(min, 33);
      total = 34;
    }
    return { rangeStart: min, totalDays: total };
  }, [effTasks]);

  const ticks = useMemo(() => buildTicks(rangeStart, totalDays, zoom), [rangeStart, totalDays, zoom]);
  const gridWidth = totalDays * px;
  const todayLeft = dayDiff(rangeStart, todayUTC()) * px;

  const tasksByPhase = useMemo(() => {
    const map = new Map<string, EffTask[]>();
    const unphased: EffTask[] = [];
    for (const t of effTasks) {
      if (t.phase_id && phases.some((p) => p.id === t.phase_id)) {
        const arr = map.get(t.phase_id) ?? [];
        arr.push(t);
        map.set(t.phase_id, arr);
      } else {
        unphased.push(t);
      }
    }
    const sortFn = (a: EffTask, b: EffTask) =>
      (a._start?.getTime() ?? Infinity) - (b._start?.getTime() ?? Infinity) || a.text.localeCompare(b.text);
    for (const arr of map.values()) arr.sort(sortFn);
    unphased.sort(sortFn);
    return { map, unphased };
  }, [effTasks, phases]);

  const sortedPhases = useMemo(() => [...phases].sort((a, b) => a.sort_order - b.sort_order), [phases]);

  // --- drag / resize ---------------------------------------------------------
  function onBarPointerDown(e: React.PointerEvent, t: EffTask, mode: DragState['mode']) {
    if (!t._start || !t._end) return;
    e.preventDefault();
    e.stopPropagation();
    dragRef.current = { taskId: t.id, mode, startX: e.clientX, origStart: t._start, origEnd: t._end };
    window.addEventListener('pointermove', onDragMove);
    window.addEventListener('pointerup', onDragEnd, { once: true });
  }

  function onDragMove(e: PointerEvent) {
    const d = dragRef.current;
    if (!d) return;
    const deltaDays = Math.round((e.clientX - d.startX) / px);
    let start = d.origStart;
    let end = d.origEnd;
    if (d.mode === 'move') {
      start = addDays(d.origStart, deltaDays);
      end = addDays(d.origEnd, deltaDays);
    } else if (d.mode === 'resize-start') {
      start = addDays(d.origStart, deltaDays);
      if (start.getTime() > end.getTime()) start = end;
    } else {
      end = addDays(d.origEnd, deltaDays);
      if (end.getTime() < start.getTime()) end = start;
    }
    setOverrides((o) => ({ ...o, [d.taskId]: { start_date: toISO(start), end_date: toISO(end) } }));
  }

  function onDragEnd() {
    window.removeEventListener('pointermove', onDragMove);
    const d = dragRef.current;
    dragRef.current = null;
    if (!d) return;
    setOverrides((o) => {
      const ov = o[d.taskId];
      if (ov) taskMutation.mutate({ id: d.taskId, body: { start_date: ov.start_date, end_date: ov.end_date } });
      return o;
    });
  }

  // Click an empty (unscheduled) task row to place a 3-day bar where clicked.
  function scheduleAt(t: EffTask, clientX: number, rowEl: HTMLElement) {
    const rect = rowEl.getBoundingClientRect();
    const dayIdx = Math.max(0, Math.floor((clientX - rect.left) / px));
    const start = addDays(rangeStart, dayIdx);
    const end = addDays(start, 2);
    setOverrides((o) => ({ ...o, [t.id]: { start_date: toISO(start), end_date: toISO(end) } }));
    taskMutation.mutate({ id: t.id, body: { start_date: toISO(start), end_date: toISO(end) } });
  }

  function submitTask(phaseId: string) {
    const text = taskDraft.trim();
    if (!text) return;
    const start = todayUTC();
    addTaskMutation.mutate({
      text,
      phase_id: phaseId,
      start_date: toISO(start),
      end_date: toISO(addDays(start, 2)),
    });
  }

  // --- render helpers --------------------------------------------------------
  function barColor(t: EffTask, phase?: ApiPhase): string {
    if (t.done) return 'var(--color-gray)';
    return phase?.color || 'var(--color-green)';
  }

  const rows: React.ReactNode[] = [];
  const leftRows: React.ReactNode[] = [];

  function pushPhase(phase: ApiPhase) {
    const phaseTasks = tasksByPhase.map.get(phase.id) ?? [];
    const collapsed = phase.collapsed;
    leftRows.push(
      <div
        key={`l-p-${phase.id}`}
        className="group flex items-center gap-1.5 border-b border-grid px-2"
        style={{ height: PHASE_ROW_H }}
      >
        <button
          onClick={() => phaseMutation.mutate({ id: phase.id, body: { collapsed: !collapsed } })}
          className="cursor-pointer border-none bg-transparent p-0 text-[10px] text-gray"
          title={collapsed ? 'Expand' : 'Collapse'}
        >
          {collapsed ? '▶' : '▼'}
        </button>
        <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: phase.source === 'stage' ? 'var(--color-violet)' : 'var(--color-blue)' }} />
        <span className="min-w-0 flex-1 truncate text-[11.5px] font-semibold text-white" title={phase.name}>
          {phase.name}
        </span>
        <span className="shrink-0 font-mono text-[10px] text-gray">{phaseTasks.length}</span>
        {phase.source === 'custom' && (
          <button
            onClick={() => delPhaseMutation.mutate(phase.id)}
            className="hidden shrink-0 cursor-pointer border-none bg-transparent p-0 text-[11px] text-gray group-hover:block hover:text-red"
            title="Delete phase"
          >
            ×
          </button>
        )}
      </div>,
    );
    rows.push(
      <div key={`r-p-${phase.id}`} className="border-b border-grid bg-panel/40" style={{ height: PHASE_ROW_H, width: gridWidth }} />,
    );
    if (collapsed) return;

    for (const t of phaseTasks) pushTask(t, phase);

    // inline add-task row for this phase
    leftRows.push(
      <div key={`l-add-${phase.id}`} className="flex items-center border-b border-grid pl-6 pr-2" style={{ height: TASK_ROW_H }}>
        {taskDraftFor === phase.id ? (
          <input
            autoFocus
            value={taskDraft}
            onChange={(e) => setTaskDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') submitTask(phase.id);
              if (e.key === 'Escape') setTaskDraftFor(null);
            }}
            onBlur={() => !taskDraft.trim() && setTaskDraftFor(null)}
            placeholder="Task name, Enter to add"
            className="w-full rounded-sm border border-grid bg-terminal-black px-1.5 py-0.5 text-[11px] text-white placeholder:text-gray"
          />
        ) : (
          <button
            onClick={() => {
              setTaskDraftFor(phase.id);
              setTaskDraft('');
            }}
            className="cursor-pointer border-none bg-transparent p-0 text-[11px] text-gray hover:text-violet"
          >
            + Add task
          </button>
        )}
      </div>,
    );
    rows.push(
      <div key={`r-add-${phase.id}`} className="border-b border-grid" style={{ height: TASK_ROW_H, width: gridWidth }} />,
    );
  }

  function pushTask(t: EffTask, phase?: ApiPhase) {
    const scheduled = t._start && t._end;
    leftRows.push(
      <label key={`l-t-${t.id}`} className="flex cursor-pointer items-center gap-2 border-b border-grid pl-6 pr-2" style={{ height: TASK_ROW_H }}>
        <input
          type="checkbox"
          checked={t.done}
          onChange={() => taskMutation.mutate({ id: t.id, body: { done: !t.done } })}
          className="h-3 w-3 shrink-0 cursor-pointer accent-violet"
        />
        <span className={`min-w-0 flex-1 truncate text-[11px] ${t.done ? 'text-gray line-through' : 'text-[#e7e7ea]'}`} title={t.text}>
          {t.text}
        </span>
      </label>,
    );

    rows.push(
      <div
        key={`r-t-${t.id}`}
        className="relative border-b border-grid"
        style={{ height: TASK_ROW_H, width: gridWidth }}
        onClick={(e) => {
          if (!scheduled) scheduleAt(t, e.clientX, e.currentTarget);
        }}
      >
        {scheduled ? (
          (() => {
            const left = dayDiff(rangeStart, t._start!) * px;
            const width = Math.max(px * 0.6, (dayDiff(t._start!, t._end!) + 1) * px);
            return (
              <div
                className="group absolute top-1/2 flex -translate-y-1/2 items-center rounded"
                style={{ left, width, height: 18, background: barColor(t, phase) }}
                onPointerDown={(e) => onBarPointerDown(e, t, 'move')}
                title={`${t.text}: ${toISO(t._start!)} → ${toISO(t._end!)}`}
              >
                <span
                  className="absolute left-0 top-0 h-full w-1.5 cursor-ew-resize rounded-l opacity-0 group-hover:opacity-100"
                  style={{ background: 'rgba(255,255,255,0.35)' }}
                  onPointerDown={(e) => onBarPointerDown(e, t, 'resize-start')}
                />
                <span className="pointer-events-none w-full cursor-grab truncate px-1.5 text-[10px] font-medium text-white">
                  {width > 60 ? t.text : ''}
                </span>
                <span
                  className="absolute right-0 top-0 h-full w-1.5 cursor-ew-resize rounded-r opacity-0 group-hover:opacity-100"
                  style={{ background: 'rgba(255,255,255,0.35)' }}
                  onPointerDown={(e) => onBarPointerDown(e, t, 'resize-end')}
                />
              </div>
            );
          })()
        ) : (
          <span className="absolute left-2 top-1/2 -translate-y-1/2 text-[10px] text-gray/60">click to schedule →</span>
        )}
      </div>,
    );
  }

  for (const phase of sortedPhases) pushPhase(phase);

  // Unphased tasks tray
  if (tasksByPhase.unphased.length > 0) {
    leftRows.push(
      <div key="l-unphased" className="flex items-center gap-1.5 border-b border-grid px-2" style={{ height: PHASE_ROW_H }}>
        <span className="min-w-0 flex-1 truncate text-[11.5px] font-semibold text-gray">No phase</span>
        <span className="shrink-0 font-mono text-[10px] text-gray">{tasksByPhase.unphased.length}</span>
      </div>,
    );
    rows.push(<div key="r-unphased" className="border-b border-grid bg-panel/40" style={{ height: PHASE_ROW_H, width: gridWidth }} />);
    for (const t of tasksByPhase.unphased) pushTask(t);
  }

  return (
    <div className="flex flex-col gap-3">
      {/* toolbar */}
      <div className="flex items-center justify-between">
        <div className="text-[11.5px] font-semibold text-white">Project Plan</div>
        <div className="flex items-center gap-2">
          <div className="flex overflow-hidden rounded border border-grid">
            {(['day', 'week', 'month'] as Zoom[]).map((z) => (
              <button
                key={z}
                onClick={() => setZoom(z)}
                className={`cursor-pointer border-none px-2.5 py-1 text-[11px] capitalize ${
                  zoom === z ? 'bg-violet text-white' : 'bg-transparent text-gray'
                }`}
              >
                {z}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="overflow-hidden rounded border border-grid bg-panel">
        <div className="flex">
          {/* left fixed column */}
          <div className="shrink-0 border-r border-grid" style={{ width: LEFT_W }}>
            <div className="flex items-center border-b border-grid px-2 text-[10px] uppercase tracking-wide text-gray" style={{ height: HEADER_H }}>
              Tasks
            </div>
            {leftRows}
          </div>

          {/* right scrollable timeline */}
          <div className="min-w-0 flex-1 overflow-x-auto">
            <div style={{ width: gridWidth, position: 'relative' }}>
              {/* header */}
              <div className="relative border-b border-grid" style={{ height: HEADER_H }}>
                {ticks.map((tk, i) => (
                  <div key={i} className="absolute top-0 h-full" style={{ left: tk.left }}>
                    <div className="h-full border-l" style={{ borderColor: tk.major ? 'var(--color-grid)' : 'rgba(42,43,51,0.5)' }} />
                    <span
                      className={`absolute left-1 top-1 whitespace-nowrap text-[9px] ${tk.major ? 'font-semibold text-[#c9c9d1]' : 'text-gray'}`}
                    >
                      {tk.label}
                    </span>
                  </div>
                ))}
              </div>
              {/* body: vertical gridlines behind rows */}
              <div className="relative">
                <div className="pointer-events-none absolute inset-0">
                  {ticks.map((tk, i) => (
                    <div
                      key={i}
                      className="absolute top-0 bottom-0 border-l"
                      style={{ left: tk.left, borderColor: tk.major ? 'var(--color-grid)' : 'rgba(42,43,51,0.4)' }}
                    />
                  ))}
                  {todayLeft >= 0 && todayLeft <= gridWidth && (
                    <div className="absolute top-0 bottom-0 border-l-2" style={{ left: todayLeft, borderColor: 'var(--color-amber)' }} />
                  )}
                </div>
                {rows}
              </div>
            </div>
          </div>
        </div>

        {/* add phase footer */}
        <div className="border-t border-grid px-2 py-1.5">
          {addingPhase ? (
            <input
              autoFocus
              value={phaseDraft}
              onChange={(e) => setPhaseDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && phaseDraft.trim()) addPhaseMutation.mutate(phaseDraft.trim());
                if (e.key === 'Escape') setAddingPhase(false);
              }}
              onBlur={() => !phaseDraft.trim() && setAddingPhase(false)}
              placeholder="Phase name, Enter to add"
              className="w-64 rounded-sm border border-grid bg-terminal-black px-2 py-1 text-[11px] text-white placeholder:text-gray"
            />
          ) : (
            <button onClick={() => setAddingPhase(true)} className="cursor-pointer border-none bg-transparent p-0 text-[11px] text-gray hover:text-violet">
              + Add phase
            </button>
          )}
        </div>
      </div>

      <div className="text-[10px] text-gray">
        Drag a bar to move it · drag its edges to resize · click an unscheduled row to place it · the amber line marks today.
      </div>
    </div>
  );
}
