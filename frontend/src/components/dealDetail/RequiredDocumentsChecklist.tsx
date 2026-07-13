import type { ApiDDItem } from '../../lib/api';

const STATUS_COLOR: Record<ApiDDItem['status'], string> = {
  pending: 'var(--color-amber)',
  received: 'var(--color-green)',
  reviewed: 'var(--color-blue)',
};

export function RequiredDocumentsChecklist({ items }: { items: ApiDDItem[] }) {
  return (
    <div>
      <div className="mb-2 text-xs font-semibold text-white">Required documents</div>
      <div className="overflow-hidden rounded border border-grid bg-panel">
        {items.length === 0 && <div className="px-4 py-3 text-[11px] text-gray">No due diligence checklist items yet.</div>}
        {items.map((item) => (
          <div key={item.id} className="flex items-center justify-between border-b border-grid px-4 py-2.5 last:border-none">
            <div className="text-xs text-white">{item.item}</div>
            <div
              className="rounded-sm border border-grid bg-terminal-black px-2 py-0.5 text-[9.5px] capitalize"
              style={{ color: STATUS_COLOR[item.status] }}
            >
              {item.status}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
