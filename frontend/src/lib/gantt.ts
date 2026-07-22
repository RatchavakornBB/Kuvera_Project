// Date + geometry helpers for the Project Plan Gantt. All dates are handled as
// UTC date-only (yyyy-mm-dd) so dragging a bar never drifts by a day across
// timezones — the grid is a calendar, not a wall clock.

export const DAY_MS = 86_400_000;

export type Zoom = 'day' | 'week' | 'month';

export const PX_PER_DAY: Record<Zoom, number> = {
  day: 34,
  week: 13,
  month: 4.6,
};

export function parseDate(s: string): Date {
  return new Date(`${s}T00:00:00Z`);
}

export function toISO(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function addDays(d: Date, n: number): Date {
  return new Date(d.getTime() + n * DAY_MS);
}

export function dayDiff(a: Date, b: Date): number {
  return Math.round((b.getTime() - a.getTime()) / DAY_MS);
}

export function todayUTC(): Date {
  return parseDate(new Date().toISOString().slice(0, 10));
}

export interface Tick {
  left: number; // px offset from range start
  label: string;
  major: boolean; // month/week boundary → darker gridline + bolder label
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

/** Vertical gridline ticks + labels for the timeline header, adapted to zoom. */
export function buildTicks(rangeStart: Date, totalDays: number, zoom: Zoom): Tick[] {
  const px = PX_PER_DAY[zoom];
  const ticks: Tick[] = [];
  for (let i = 0; i < totalDays; i++) {
    const d = addDays(rangeStart, i);
    const dow = d.getUTCDay();
    const dom = d.getUTCDate();
    const left = i * px;
    if (zoom === 'day') {
      ticks.push({ left, label: `${WEEKDAYS[dow]} ${dom}`, major: dom === 1 });
    } else if (zoom === 'week') {
      if (dow === 1) ticks.push({ left, label: `${MONTHS[d.getUTCMonth()]} ${dom}`, major: dom <= 7 });
    } else {
      if (dom === 1) ticks.push({ left, label: `${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`, major: true });
    }
  }
  // For week/month, add a leading label at the range start only when the first
  // boundary tick is far enough away to not collide with it.
  if (zoom !== 'day') {
    const firstBoundary = ticks[0]?.left ?? Infinity;
    if (firstBoundary > 5 * px) {
      const label =
        zoom === 'week'
          ? `${MONTHS[rangeStart.getUTCMonth()]} ${rangeStart.getUTCDate()}`
          : `${MONTHS[rangeStart.getUTCMonth()]} ${rangeStart.getUTCFullYear()}`;
      ticks.unshift({ left: 0, label, major: false });
    }
  }
  return ticks;
}
