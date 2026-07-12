"""Startup config validation — fails fast with the missing key name.

Never let a missing key surface as a silent mid-request failure during a
demo (AGENT.md Section 1). Every route/service reads settings from here,
never straight from os.environ.
"""

import os

from dotenv import load_dotenv

load_dotenv()

REQUIRED_KEYS = ["ANTHROPIC_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
OPTIONAL_KEYS = ["OPENAI_API_KEY", "GOOGLE_API_KEY", "DEEPGRAM_API_KEY"]


class Settings:
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
        self.deepgram_api_key = os.environ.get("DEEPGRAM_API_KEY")


settings = Settings()
