"""The one Supabase client instance every service imports — no bare
supabase calls from routes (AGENT.md Section 7 step 4)."""

from functools import lru_cache

from supabase import Client, create_client

from app.config import settings


@lru_cache
def get_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_key)
