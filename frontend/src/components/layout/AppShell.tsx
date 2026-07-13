import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';
import { ChatPanel } from '../chat/ChatPanel';
import { useChatSocket } from '../../lib/useChatSocket';

export interface ShellContext {
  askAboutDeal: (dealId: string, dealName: string) => void;
}

export function AppShell() {
  const [chatOpen, setChatOpen] = useState(false);
  const [dealContext, setDealContext] = useState<{ id: string; name: string } | undefined>();
  const { messages, busy, send } = useChatSocket();

  const askAboutDeal: ShellContext['askAboutDeal'] = (dealId, dealName) => {
    setDealContext({ id: dealId, name: dealName });
    setChatOpen(true);
  };

  return (
    <div className="flex h-screen flex-col bg-terminal-black text-[#e7e7ea]">
      <TopBar onToggleChat={() => setChatOpen((v) => !v)} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <div className="flex-1 overflow-y-auto">
          <Outlet context={{ askAboutDeal } satisfies ShellContext} />
        </div>
        {chatOpen && (
          <ChatPanel
            messages={messages}
            agentBusyLabel={busy ? 'Kuvera Assistant · thinking…' : undefined}
            dealContextLabel={dealContext?.name}
            onClearContext={() => setDealContext(undefined)}
            onSend={(text) => send(text, dealContext?.id)}
          />
        )}
      </div>
    </div>
  );
}
