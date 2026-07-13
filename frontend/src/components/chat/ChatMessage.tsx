import type { ChatArtifact } from './ChatArtifactCard';

export interface ChatMessageData {
  id: string;
  role: 'assistant' | 'user';
  text: string;
  artifact?: ChatArtifact;
}

export function ChatMessage({ message }: { message: ChatMessageData }) {
  if (message.role === 'assistant') {
    return (
      <div className="max-w-[82%] self-start rounded-sm border-l-2 border-violet bg-panel px-3.5 py-3 text-[13px] leading-relaxed text-[#e7e7ea]">
        {message.text}
      </div>
    );
  }

  return (
    <div className="max-w-[82%] self-end rounded-sm bg-grid px-3.5 py-3 text-[13px] leading-relaxed text-[#e7e7ea]">
      {message.text}
    </div>
  );
}
