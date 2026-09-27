from typing import Protocol


class RateLimiter(Protocol):
    """Integration boundary for endpoint-specific distributed rate limiting."""

    def check(self, key: str, *, limit: int, window_seconds: int) -> None: ...

