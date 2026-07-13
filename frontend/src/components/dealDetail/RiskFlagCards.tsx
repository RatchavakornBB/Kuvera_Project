import type { AnalyzeResult } from '../../lib/api';

type RiskFlag = AnalyzeResult['risk_flags'][number];

const SEVERITY_ORDER = ['high', 'medium'] as const;
const SEVERITY_COLOR: Record<string, string> = {
  high: 'var(--color-red)',
  medium: 'var(--color-amber)',
};
const SEVERITY_LABEL: Record<string, string> = {
  high: 'High severity',
  medium: 'Medium severity',
};

export function RiskFlagCards({ flags }: { flags: RiskFlag[] }) {
  if (flags.length === 0) {
    return (
      <div className="rounded border border-grid bg-panel p-4">
        <div className="mb-2 text-[11.5px] font-semibold text-white">Risk flags</div>
        <div className="text-[11px] text-gray">No risk flags on the latest analysis.</div>
      </div>
    );
  }

  const bySeverity = SEVERITY_ORDER.map((severity) => ({
    severity,
    items: flags.filter((f) => f.severity === severity),
  })).filter((group) => group.items.length > 0);

  return (
    <div className="rounded border border-grid bg-panel p-4">
      <div className="mb-3 text-[11.5px] font-semibold text-white">Risk flags</div>
      <div className="flex flex-col gap-3">
        {bySeverity.map((group) => (
          <div key={group.severity}>
            <div
              className="mb-1.5 text-[9.5px] font-semibold uppercase tracking-wide"
              style={{ color: SEVERITY_COLOR[group.severity] }}
            >
              {SEVERITY_LABEL[group.severity]} ({group.items.length})
            </div>
            <div className="flex flex-col gap-2">
              {group.items.map((flag, i) => (
                <div
                  key={i}
                  className="rounded border-l-2 bg-terminal-black px-3 py-2"
                  style={{ borderColor: SEVERITY_COLOR[group.severity] }}
                >
                  <div className="text-[11.5px] text-[#e7e7ea]">{flag.description}</div>
                  {flag.source_excerpt && (
                    <div className="mt-1 line-clamp-2 text-[10px] italic text-gray">“{flag.source_excerpt}”</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
