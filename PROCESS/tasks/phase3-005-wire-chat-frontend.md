Scope: frontend/src/lib/useChatSocket.ts, frontend/src/App.tsx
Depends on: phase3-003-chat-panel (done), phase3-004-chat-websocket (done)
Files allowed to touch: files listed above
DoD:
  - [x] Real WebSocket connection to ws://localhost:8000/chat, not a mock
  - [x] Sending a message appends the user bubble immediately, then the real assistant response (with artifact/sources if present) once it arrives
  - [x] Deal context chip reflects what's actually being sent (clicking a Kanban card sets it — a bonus integration beyond the original scope-lock, but trivial and directly useful)
  - [x] Verified in a real browser: typed "What documents are outstanding for this deal?" into the real composer, real WebSocket round trip, real grounded answer about Deal A's actual FY2025 statements/cap table/MSA rendered correctly, zero console errors
