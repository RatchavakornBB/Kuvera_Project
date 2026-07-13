import { useState } from 'react';

interface ChatComposerProps {
  dealContextLabel?: string;
  onClearContext?: () => void;
  onSend: (text: string) => void;
  onAttachFile?: (file: File) => void;
}

export function ChatComposer({ dealContextLabel, onClearContext, onSend, onAttachFile }: ChatComposerProps) {
  const [text, setText] = useState('');

  function send() {
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setText('');
  }

  return (
    <div className="flex flex-col gap-2 border-t border-grid pt-3">
      {dealContextLabel && (
        <div className="flex items-center gap-1.5 rounded border border-grid bg-terminal-black px-2 py-1.5">
          <div className="text-[10px] text-gray">Scoped to</div>
          <div className="flex-1 text-[10.5px] text-violet">{dealContextLabel}</div>
          <button onClick={onClearContext} className="cursor-pointer border-none bg-transparent text-[11px] text-gray">
            &times;
          </button>
        </div>
      )}
      <div className="flex items-center gap-2">
        <label className="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded border border-grid">
          <div className="h-3.5 w-3.5 rounded-sm border-[1.5px] border-gray" />
          <input
            type="file"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) onAttachFile?.(file);
              e.target.value = '';
            }}
          />
        </label>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Ask about a deal, document, or company..."
          className="flex-1 rounded border border-grid bg-panel px-3.5 py-2.5 text-[13px] text-[#e7e7ea] outline-none"
        />
        <button
          onClick={send}
          className="cursor-pointer rounded border-none bg-violet px-4.5 py-2.5 text-xs font-semibold text-white"
        >
          Send
        </button>
      </div>
    </div>
  );
}
