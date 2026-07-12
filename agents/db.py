"""Supabase client for agents/ — mirrors backend/app/db.py's pattern but
stays import-independent of the backend package (D-007)."""

from functools import lru_cache

from supabase import Client, create_client

from agents.config import settings


@lru_cache
def get_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_key)
