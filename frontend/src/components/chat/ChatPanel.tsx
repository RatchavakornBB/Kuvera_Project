import { useState } from 'react';
import { ChatMessage, type ChatMessageData } from './ChatMessage';
import { ChatArtifactCard } from './ChatArtifactCard';
import { ChatComposer } from './ChatComposer';
import { AgentActivityPill } from './AgentActivityPill';

interface ChatPanelProps {
  messages: ChatMessageData[];
  agentBusyLabel?: string;
  traceText?: string;
  dealContextLabel?: string;
  onClearContext?: () => void;
  onSend: (text: string) => void;
  onAttachFile?: (file: File) => void;
  onOpenArtifact?: (artifact: ChatMessageData['artifact']) => void;
}

export function ChatPanel({
  messages,
  agentBusyLabel,
  traceText,
  dealContextLabel,
  onClearContext,
  onSend,
  onAttachFile,
  onOpenArtifact,
}: ChatPanelProps) {
  const [traceOpen, setTraceOpen] = useState(false);

  return (
    <div className="flex h-full w-[340px] flex-col border-l border-grid bg-panel">
      <div className="flex items-center gap-2 border-b border-grid px-4 py-3.5">
        <div className="h-2 w-2 rounded-full bg-violet" />
        <div className="text-[12.5px] font-semibold text-white">Kuvera Assistant</div>
        <div className="flex-1" />
        {traceText && (
          <button
            onClick={() => setTraceOpen((v) => !v)}
            className="cursor-pointer border-none bg-transparent text-[10px] text-gray"
          >
            View agent activity
          </button>
        )}
      </div>

      {traceOpen && traceText && (
        <div className="border-b border-grid bg-terminal-black px-4 py-2.5 font-mono text-[10px] text-gray">
          {traceText}
        </div>
      )}

      <div className="flex flex-1 flex-col gap-2.5 overflow-y-auto px-4 py-3.5">
        {messages.map((m) => (
          <div key={m.id} className="flex flex-col">
            <ChatMessage message={m} />
            {m.artifact && <ChatArtifactCard artifact={m.artifact} onOpen={() => onOpenArtifact?.(m.artifact)} />}
          </div>
        ))}
        {agentBusyLabel && <AgentActivityPill label={agentBusyLabel} />}
      </div>

      <div className="px-4 pb-4">
        <ChatComposer
          dealContextLabel={dealContextLabel}
          onClearContext={onClearContext}
          onSend={onSend}
          onAttachFile={onAttachFile}
        />
      </div>
    </div>
  );
}
