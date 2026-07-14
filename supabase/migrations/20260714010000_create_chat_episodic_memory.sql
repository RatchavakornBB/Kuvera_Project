-- Episodic chat memory (user-requested) — real persistent conversation history per deal,
-- multiple conversation "tabs" per deal, every message embedded immediately for real RAG search
-- over past chat, and an automatic Knowledge Agent digest that synthesizes accumulated chat into
-- knowledge_base once a conversation accumulates enough new messages.

create table public.chat_conversations (
  id uuid primary key default gen_random_uuid(),
  deal_id uuid not null references public.deals(id) on delete cascade,
  title text,
  -- How many of this conversation's messages have already been folded into a
  -- knowledge_base digest — the digest trigger only fires on genuinely new
  -- material, never re-summarizes the same messages twice.
  digested_message_count int not null default 0,
  created_at timestamptz not null default now(),
  last_message_at timestamptz not null default now()
);

create table public.chat_messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.chat_conversations(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  text text not null,
  sources jsonb,
  artifact jsonb,
  -- voyage-3, 1024-dim (agents/embeddings.py) — embedded immediately on every
  -- message, not batched/periodic, so RAG search over chat history is never
  -- stale by more than one write.
  embedding vector(1024),
  created_at timestamptz not null default now()
);

create index chat_conversations_deal_id_idx on public.chat_conversations(deal_id);
create index chat_messages_conversation_id_idx on public.chat_messages(conversation_id);
create index chat_messages_embedding_idx
  on public.chat_messages using hnsw (embedding vector_cosine_ops);

grant select, insert, update, delete on public.chat_conversations to service_role;
grant select, insert, update, delete on public.chat_messages to service_role;

-- Chat-derived knowledge needs its own category — distinct from the deal-close-time categories,
-- since this is synthesized from ongoing conversation, not a one-time deal outcome promotion.
alter table public.knowledge_base drop constraint knowledge_base_category_check;
alter table public.knowledge_base add constraint knowledge_base_category_check check (category in (
  'deal_profile', 'industry_insight', 'company_insight', 'competitor_insight',
  'evaluation_approach', 'analysis_approach', 'strategy_planning_approach',
  'outcome', 'risk_signals_resolution', 'prompt_engineering', 'loop_engineering',
  'chat_insights'
));
