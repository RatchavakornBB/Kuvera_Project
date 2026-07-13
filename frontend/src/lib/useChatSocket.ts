import { useEffect, useRef, useState } from 'react';
import type { ChatMessageData } from '../components/chat/ChatMessage';

const WS_URL = (import.meta.env.VITE_WS_URL as string | undefined) ?? 'ws://localhost:8000/chat';

interface ServerMessage {
  role: 'assistant';
  text: string;
  sources?: string[];
  artifact?: { title: string; type: string };
}

export function useChatSocket() {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [busy, setBusy] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const socket = new WebSocket(WS_URL);
    socketRef.current = socket;

    socket.onmessage = (event) => {
      const data: ServerMessage = JSON.parse(event.data);
      setBusy(false);
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: 'assistant', text: data.text, artifact: data.artifact },
      ]);
    };

    return () => socket.close();
  }, []);

  function send(text: string, dealId?: string) {
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'user', text }]);
    setBusy(true);
    socketRef.current?.send(JSON.stringify({ message: text, deal_id: dealId }));
  }

  return { messages, busy, send };
}
