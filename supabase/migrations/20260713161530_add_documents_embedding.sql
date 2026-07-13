-- Documents & Contracts screen semantic search (closes the substring-search deviation logged in
-- phase4-002's report). Reuses the same Voyage AI embeddings infra as knowledge_base
-- (agents/embeddings.py, voyage-3, 1024-dim) rather than a second embeddings pipeline.

alter table public.documents add column embedding vector(1024);

create index documents_embedding_idx
  on public.documents using hnsw (embedding vector_cosine_ops);
