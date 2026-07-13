import { diffLines } from '../../lib/diff';

export function DiffView({ oldText, newText }: { oldText: string; newText: string }) {
  const lines = diffLines(oldText, newText);

  if (lines.every((l) => l.type === 'same')) {
    return <div className="text-[10.5px] text-gray">No changes.</div>;
  }

  return (
    <div className="overflow-hidden rounded-sm border border-grid bg-terminal-black font-mono text-[10.5px] leading-relaxed">
      {lines.map((line, i) => (
        <div
          key={i}
          className={`whitespace-pre-wrap px-2 py-0.5 ${
            line.type === 'added'
              ? 'bg-green/10 text-green'
              : line.type === 'removed'
                ? 'bg-red/10 text-red'
                : 'text-gray'
          }`}
        >
          {line.type === 'added' ? '+ ' : line.type === 'removed' ? '- ' : '  '}
          {line.text || ' '}
        </div>
      ))}
    </div>
  );
}
