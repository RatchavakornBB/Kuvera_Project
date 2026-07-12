export type StageStatus = 'done' | 'current' | 'future';

export interface StageSegment {
  name: string;
  status: StageStatus;
  days?: number;
}

export type StageDiagramVariant = 'compact' | 'full';

interface StageDiagramProps {
  segments: StageSegment[];
  variant?: StageDiagramVariant;
}

const STAGE_SHORT = ['Lead', 'NDA', 'Sourcing', 'Valuation', 'Strategy', 'Diligence', 'Closing'];

function segmentStyle(status: StageStatus) {
  if (status === 'done') {
    return { background: 'var(--color-grid)', borderColor: 'var(--color-grid)', labelColor: 'var(--color-gray)' };
  }
  if (status === 'current') {
    return { background: 'var(--color-violet)', borderColor: 'var(--color-violet)', labelColor: 'var(--color-violet)' };
  }
  return { background: 'transparent', borderColor: 'var(--color-grid)', labelColor: 'var(--color-gray)' };
}

function segmentTitle(segment: StageSegment) {
  if (segment.status === 'future') return `${segment.name} — not started`;
  if (segment.days != null) return `${segment.name} — ${segment.days} day${segment.days === 1 ? '' : 's'}`;
  return segment.name;
}

export function StageDiagram({ segments, variant = 'compact' }: StageDiagramProps) {
  const showLabels = variant === 'full';
  const barHeight = variant === 'full' ? '7px' : '4px';

  return (
    <div className="flex w-full items-center gap-0.5">
      {segments.map((segment, i) => {
        const style = segmentStyle(segment.status);
        return (
          <div key={segment.name} title={segmentTitle(segment)} className="flex min-w-0 flex-1 flex-col items-center gap-[3px]">
            <div
              className="w-full rounded-sm border"
              style={{ height: barHeight, background: style.background, borderColor: style.borderColor }}
            />
            {showLabels && (
              <div
                className="w-full overflow-hidden text-ellipsis whitespace-nowrap text-center text-[8.5px] leading-tight"
                style={{ color: style.labelColor }}
              >
                {STAGE_SHORT[i] ?? segment.name}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
