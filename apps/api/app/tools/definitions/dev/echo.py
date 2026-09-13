"""test.echo -- the Tool Framework's own proof: a tool defined by
nothing but this file and a prompt, exercised through the exact same
registry, run endpoint, and `<ToolRunner>` component every real tool
uses. If adding this tool needed a single line of bespoke frontend or
router code, the framework would be the thing to fix, not this file.

Hidden from everyone except an admin with the `dev.playground` flag
(see `app/tools/service.py`'s `_HIDDEN_TOOL_PREFIX` check) -- the same
gate `app/routers/internal.py`'s developer playground uses, applied
generically to any tool id starting with `test.`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Input(_StrictModel):
    user_supplied_text: str = Field(title="Text to echo")


class _Section(_StrictModel):
    body: str


class _Output(_StrictModel):
    sections: list[_Section] = Field(min_length=1, max_length=1)


DEFINITION = ToolDefinition(
    id="test.echo",
    hub=Hub.PROFILE,
    name="Echo (dev only)",
    short_description="Throwaway tool proving the framework needs no bespoke code for a new tool.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="test.echo.v1",
    required_context=[ContextKey.USER_SUPPLIED_TEXT],
    result_renderer=ResultRenderer.DOCUMENT,
    save_as=AssetType.TEMPLATE,
)
