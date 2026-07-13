"""Real embeddings for the Knowledge Agent's pgvector semantic search
(system-architecture.md Section 10.1/10.2) — Voyage AI, Anthropic's
recommended embeddings pairing (Claude has no public embeddings endpoint of
its own). Fails loudly if VOYAGER_API_KEY is missing or the call errors —
no silent fallback to a zero vector or a fake similarity score."""

import httpx

from agents.config import settings

VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
MODEL = "voyage-3"
EMBEDDING_DIM = 1024


def embed_texts(texts: list[str], input_type: str = "document") -> list[list[float]]:
    """Batches every text into ONE Voyage call — not just an efficiency win,
    but load-bearing: a free-tier Voyage key has a low requests-per-minute
    limit, and calling embed once per record (e.g. once per knowledge_base
    row during a promotion) hits a real 429 (reproduced during development).
    input_type: 'document' when embedding text to be stored/searched over,
    'query' when embedding a search query — Voyage tunes the embedding
    differently for each, and using the right one measurably improves
    retrieval quality."""
    if not settings.voyage_api_key:
        raise RuntimeError(
            "VOYAGER_API_KEY is not set — the Knowledge Agent's embeddings cannot run without it. "
            "Add it to .env; there is no fallback to a fake or zero embedding."
        )
    if not texts:
        return []

    response = httpx.post(
        VOYAGE_URL,
        headers={"Authorization": f"Bearer {settings.voyage_api_key}"},
        json={"input": texts, "model": MODEL, "input_type": input_type},
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()
    embeddings = [item["embedding"] for item in sorted(data["data"], key=lambda item: item["index"])]
    for embedding in embeddings:
        if len(embedding) != EMBEDDING_DIM:
            raise RuntimeError(
                f"Voyage returned a {len(embedding)}-dim embedding, expected {EMBEDDING_DIM} "
                f"for model {MODEL!r} — the knowledge_base.embedding column won't accept this."
            )
    return embeddings


def embed_text(text: str, input_type: str = "document") -> list[float]:
    return embed_texts([text], input_type=input_type)[0]
