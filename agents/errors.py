"""AGENT.md Section 10: node failures are never silent. A node gets a
bounded number of attempts, then fails loud with a typed error carrying
which node, which attempt, and the real underlying reason — never
swallowed into an empty/default value."""


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
