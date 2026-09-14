"""A minimal in-memory circuit breaker, one instance per process.

Not backed by the database on purpose: a circuit breaker is a hint about
*this process's* recent experience talking to a provider, not durable
state — restarting the process (or running behind multiple workers, each
with its own view) is an acceptable trade for not adding a write on every
single provider call just to track transient health.
"""

from __future__ import annotations

import time


class CircuitBreaker:
    def __init__(self, *, failure_threshold: int = 5, cooldown_seconds: float = 30.0) -> None:
        self._failure_threshold = failure_threshold
        self._cooldown_seconds = cooldown_seconds
        self._failures: dict[str, int] = {}
        self._opened_at: dict[str, float] = {}

    def is_open(self, provider_name: str) -> bool:
        opened_at = self._opened_at.get(provider_name)
        if opened_at is None:
            return False
        if time.monotonic() - opened_at >= self._cooldown_seconds:
            # Cooldown elapsed: half-open — let the next call through as a
            # trial and reset bookkeeping so a single success clears it.
            del self._opened_at[provider_name]
            self._failures[provider_name] = 0
            return False
        return True

    def record_success(self, provider_name: str) -> None:
        self._failures[provider_name] = 0
        self._opened_at.pop(provider_name, None)

    def record_failure(self, provider_name: str) -> None:
        count = self._failures.get(provider_name, 0) + 1
        self._failures[provider_name] = count
        if count >= self._failure_threshold:
            self._opened_at[provider_name] = time.monotonic()

    def snapshot(self) -> dict[str, dict[str, object]]:
        """Read-only view for the admin panel's platform health page
        (app/admin/platform_health.py) -- every provider this process has
        ever recorded a failure for, and whether it's currently open."""
        return {
            provider_name: {
                "failures": self._failures.get(provider_name, 0),
                "open": self.is_open(provider_name),
            }
            for provider_name in {*self._failures, *self._opened_at}
        }


circuit_breaker = CircuitBreaker()
