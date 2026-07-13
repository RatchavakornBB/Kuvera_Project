export type DashboardView = 'board' | 'table' | 'pipeline';

const VIEWS: { key: DashboardView; label: string }[] = [
  { key: 'board', label: 'Board' },
  { key: 'table', label: 'Table' },
  { key: 'pipeline', label: 'Pipeline' },
];

export function ViewToggle({ value, onChange }: { value: DashboardView; onChange: (v: DashboardView) => void }) {
  return (
    <div className="flex rounded border border-grid bg-panel p-0.5">
      {VIEWS.map((v) => (
        <button
          key={v.key}
          onClick={() => onChange(v.key)}
          className={`cursor-pointer rounded-sm border-none px-3 py-1.5 text-[11.5px] ${
            value === v.key ? 'bg-grid text-white' : 'bg-transparent text-[#e7e7ea]'
          }`}
        >
          {v.label}
        </button>
      ))}
    </div>
  );
}
