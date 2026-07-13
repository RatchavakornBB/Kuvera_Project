import { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';
import { useChatSocket } from '../../lib/useChatSocket';
import type { ChatMessageData } from '../chat/ChatMessage';

export interface ShellContext {
  askAboutDeal: (dealId: string, dealName: string) => void;
  chat: {
    messages: ChatMessageData[];
    busy: boolean;
    send: (text: string, dealId?: string) => void;
  };
  selectedDeal?: { id: string; name: string };
  setSelectedDeal: (deal: { id: string; name: string } | undefined) => void;
}

export function AppShell() {
  const navigate = useNavigate();
  const [selectedDeal, setSelectedDeal] = useState<{ id: string; name: string } | undefined>();
  const { messages, busy, send } = useChatSocket();

  const askAboutDeal: ShellContext['askAboutDeal'] = (dealId, dealName) => {
    setSelectedDeal({ id: dealId, name: dealName });
    navigate('/chat');
  };

  const context: ShellContext = {
    askAboutDeal,
    chat: { messages, busy, send },
    selectedDeal,
    setSelectedDeal,
  };

  return (
    <div className="flex h-screen flex-col bg-terminal-black text-[#e7e7ea]">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <div className="min-w-0 flex-1 overflow-y-auto">
          <Outlet context={context} />
        </div>
      </div>
    </div>
  );
}
