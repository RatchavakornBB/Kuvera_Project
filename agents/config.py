"""Standalone settings for the agents/ package — deliberately independent
of backend/app/config.py so LangGraph nodes can be run and tested standalone
(timeline Section 6 Phase 2: "tested standalone against a real uploaded
PDF"), not only from inside the FastAPI process. Same fail-fast pattern as
the backend's config.
"""

import os

from dotenv import load_dotenv

load_dotenv()

REQUIRED_KEYS = ["ANTHROPIC_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]


class AgentSettings:
    def __init__(self) -> None:
        missing = [key for key in REQUIRED_KEYS if not os.environ.get(key)]
        if missing:
            raise RuntimeError(
                "Missing required environment variable(s): "
                f"{', '.join(missing)}. Copy .env.example to .env and fill them in."
            )
        self.anthropic_api_key = os.environ["ANTHROPIC_API_KEY"]
        self.supabase_url = os.environ["SUPABASE_URL"]
        self.supabase_key = os.environ["SUPABASE_KEY"]
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.google_api_key = os.environ.get("GOOGLE_API_KEY")


settings = AgentSettings()
