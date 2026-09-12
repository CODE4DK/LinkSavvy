"""Reads `config/models.yaml` and hands back bound provider instances.

This is the only module that knows the shape of `config/models.yaml` and
the only place `(tier, plan)` turns into a concrete `(provider, model)`
pair. The gateway asks for a provider by tier and plan; it never sees a
model string.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.ai.providers.base import LLMProvider, ModelTier
from app.ai.providers.fake_provider import FakeProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.openai_provider import OpenAIProvider

DEFAULT_MODELS_PATH = Path(__file__).resolve().parents[3] / "config" / "models.yaml"

_PROVIDER_CLASSES: dict[str, type[OpenAIProvider] | type[GeminiProvider] | type[FakeProvider]] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "fake": FakeProvider,
}


@lru_cache(maxsize=1)
def _load_config(path: str = str(DEFAULT_MODELS_PATH)) -> dict[str, Any]:
    raw: dict[str, Any] = yaml.safe_load(Path(path).read_text())
    for tier in ModelTier:
        if tier.value not in raw["tiers"]:
            raise ValueError(f"config/models.yaml is missing tier {tier.value!r}")
        for plan in ("free", "pro"):
            if plan not in raw["tiers"][tier.value]:
                raise ValueError(f"config/models.yaml tier {tier.value!r} is missing plan {plan!r}")
    return raw


@lru_cache(maxsize=32)
def _build_provider(provider_name: str, model: str) -> LLMProvider:
    # Real classes by default; tests monkeypatch _PROVIDER_CLASSES itself
    # (see tests/conftest.py's autouse _fake_ai_providers fixture) so this
    # function never has to know it's running under test.
    provider_class = _PROVIDER_CLASSES[provider_name]
    return provider_class(model=model)


def resolve_provider(tier: ModelTier, plan: str) -> LLMProvider:
    """The primary provider for a `(tier, plan)` pair."""
    config = _load_config()
    entry = config["tiers"][tier.value][plan]
    return _build_provider(entry["provider"], entry["model"])


def resolve_secondary_provider() -> LLMProvider:
    """The fallback provider used when the primary is unavailable — always
    served at a fixed model, independent of tier or plan, since a down
    provider can't be trusted to size its response to the caller's tier."""
    config = _load_config()
    return _build_provider(config["secondary_provider"], config["secondary_fallback_model"])


def tier_timeout_seconds(tier: ModelTier) -> float:
    config = _load_config()
    return float(config["timeouts_seconds"][tier.value])


def currency() -> str:
    config = _load_config()
    return str(config["currency"])


def cost_per_million_tokens_minor(model: str) -> tuple[int, int]:
    """Returns `(input_rate, output_rate)` in minor currency units per
    million tokens. Falls back to zero-cost for an unrecognized model
    (e.g. a fixture-only fake model) rather than raising — cost accounting
    degrading to zero is safe; refusing to record an invocation isn't."""
    config = _load_config()
    rates = config["costs_per_million_tokens_minor"].get(model)
    if rates is None:
        return 0, 0
    return int(rates["input"]), int(rates["output"])
