"""Renders a prompt body with no arbitrary attribute or item access.

A prompt template only ever does `{{ some_context_key }}` substitution —
never `{{ value.attr }}` or `{{ value['key'] }}`. That's a deliberate
restriction, not an oversight: every context value the gateway hands to a
template is already a flat, sanitized string wrapped in delimiters (see
`app/ai/safety/sanitize.py`), so there is nothing legitimate for a
template to reach into. Blocking attribute/item access entirely closes off
a whole class of template-injection tricks (`{{ ''.__class__ ... }}` and
friends) without needing to trust a denylist.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from jinja2 import StrictUndefined
from jinja2.exceptions import SecurityError, TemplateError
from jinja2.sandbox import SandboxedEnvironment

from app.ai.prompts.models import PromptTemplate


class _NoAttributeAccessEnvironment(SandboxedEnvironment):
    def getattr(self, obj: Any, attribute: str) -> Any:
        raise SecurityError(f"attribute access is not allowed in prompt templates: .{attribute}")

    def getitem(self, obj: Any, argument: Any) -> Any:
        raise SecurityError(f"item access is not allowed in prompt templates: [{argument!r}]")


_ENV = _NoAttributeAccessEnvironment(autoescape=False, undefined=StrictUndefined)


class PromptRenderError(Exception):
    pass


def render_prompt(template: PromptTemplate, context: Mapping[str, str]) -> str:
    try:
        compiled = _ENV.from_string(template.body)
        return compiled.render(**context)
    except (TemplateError, SecurityError) as exc:
        raise PromptRenderError(f"failed to render prompt {template.id!r}: {exc}") from exc
