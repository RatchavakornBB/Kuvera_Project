"""AGENT.md Section 10: node failures are never silent. A node gets a
bounded number of attempts, then fails loud with a typed error carrying
which node, which attempt, and the real underlying reason — never
swallowed into an empty/default value."""

import json


class NodeFailure(Exception):
    def __init__(self, node: str, attempts: int, reason: str, raw_error: str):
        self.node = node
        self.attempts = attempts
        self.reason = reason
        self.raw_error = raw_error
        super().__init__(f"{node} failed after {attempts} attempt(s): {reason} ({raw_error})")

    def to_dict(self) -> dict:
        return {
            "node": self.node,
            "attempts": self.attempts,
            "reason": self.reason,
            "raw_error": self.raw_error,
        }


class LoopTruncated(NodeFailure):
    """A multi-step agentic loop (agents/loop_runner.py) hit max_iterations
    while the model still wanted to call a non-terminal tool. A NodeFailure
    subclass — deliberately, not a sibling exception — so every existing
    `except NodeFailure` handler across the route layer (analyze.py,
    contracts.py, chat.py's websocket handler, etc.) already catches this
    without any of those files needing to learn about a second error type.
    Carries the step trajectory on top of NodeFailure's node/attempts/reason/
    raw_error, so the caller has the full picture, not just "it timed out"."""

    def __init__(self, node: str, max_iterations: int, steps: list):
        self.max_iterations = max_iterations
        self.steps = steps
        super().__init__(
            node=node,
            attempts=max_iterations,
            reason="loop truncated — model still wanted a tool after the iteration cap",
            raw_error=json.dumps(steps, default=str)[:2000],
        )

    def to_dict(self) -> dict:
        return {**super().to_dict(), "max_iterations": self.max_iterations, "steps": self.steps}
