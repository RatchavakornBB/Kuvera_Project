-- Real source-URL tracking for documents added via "+ Add link" (NotebookLM-style URL sources,
-- Chat page Sources panel). NULL for every ordinary file upload — only set when the document's
-- real content was fetched from the web rather than uploaded as a file.

alter table public.documents add column source_url text;
