from typing import Any

from agents.learning_agent import list_digests as _list_digests
from agents.learning_agent import run_learning_cycle


def run_cycle(category: str, topic: str) -> dict[str, Any]:
    return run_learning_cycle(category, topic)


def list_digests() -> list[dict[str, Any]]:
    return _list_digests()
