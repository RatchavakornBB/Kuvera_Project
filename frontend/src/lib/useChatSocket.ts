import { useEffect, useRef, useState } from 'react';
import type { ChatMessageData } from '../components/chat/ChatMessage';
import { fetchConversationMessages } from './api';

const WS_URL = (import.meta.env.VITE_WS_URL as string | undefined) ?? 'ws://localhost:8000/chat';

// Comfortably longer than the backend's own 120s per-call timeout
// (agents/adapters/model_adapter.py) plus retry/network round trip — a
// real live hang was observed where a lost/stuck request left the UI
// showing "thinking..." indefinitely with no way to recover short of a
// page refresh. This ensures the user always gets feedback within a
// bounded time even if the WebSocket message or response is silently lost.
const RESPONSE_TIMEOUT_MS = 150_000;

interface ServerMessage {
  role: 'assistant';
  text: string;
  sources?: string[];
  artifact?: { title: string; type: string; deal_id?: string };
  conversation_id?: string;
}

export function useChatSocket() {
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [busy, setBusy] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const conversationIdRef = useRef<string | undefined>(undefined);
  conversationIdRef.current = conversationId;

  useEffect(() => {
    const socket = new WebSocket(WS_URL);
    socketRef.current = socket;

    socket.onmessage = (event) => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      const data: ServerMessage = JSON.parse(event.data);
      setBusy(false);
      // A brand-new conversation is auto-created server-side on first
      // message — pick up its real id so the next send() in this tab
      // continues the same persisted conversation instead of starting
      // a new one every turn.
      if (data.conversation_id && data.conversation_id !== conversationIdRef.current) {
        setConversationId(data.conversation_id);
      }
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: 'assistant', text: data.text, artifact: data.artifact },
      ]);
    };

    return () => {
      socket.close();
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  function send(text: string, dealId?: string) {
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'user', text }]);
    setBusy(true);
    socketRef.current?.send(JSON.stringify({ message: text, deal_id: dealId, conversation_id: conversationId }));

    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setBusy(false);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          text: "This is taking much longer than expected and may have stalled — try again, or refresh if it doesn't respond.",
        },
      ]);
    }, RESPONSE_TIMEOUT_MS);
  }

  async function switchConversation(newConversationId: string) {
    setConversationId(newConversationId);
    const history = await fetchConversationMessages(newConversationId);
    setMessages(
      history.map((m) => ({
        id: m.id,
        role: m.role,
        text: m.text,
        artifact: m.artifact ?? undefined,
      })),
    );
  }

  function startNewConversation() {
    setConversationId(undefined);
    setMessages([]);
  }

  return { conversationId, messages, busy, send, switchConversation, startNewConversation };
}
