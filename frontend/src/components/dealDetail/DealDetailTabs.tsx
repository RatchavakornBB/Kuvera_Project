export type DealTab = 'overview' | 'documents' | 'analysis' | 'tasks';

const TABS: { key: DealTab; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'documents', label: 'Documents' },
  { key: 'analysis', label: 'Analysis' },
  { key: 'tasks', label: 'Tasks & Notes' },
];

export function DealDetailTabs({ value, onChange }: { value: DealTab; onChange: (t: DealTab) => void }) {
  return (
    <div className="flex gap-0.5 border-b border-grid">
      {TABS.map((t) => (
        <button
          key={t.key}
          onClick={() => onChange(t.key)}
          className={`cursor-pointer border-none border-b-2 bg-transparent px-3.5 py-2 text-xs ${
            value === t.key ? 'border-violet text-white' : 'border-transparent text-gray'
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
