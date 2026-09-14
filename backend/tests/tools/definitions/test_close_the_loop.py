"""B3: audits that every hub's "Save" lands in the right Workspace
collection with a useful, non-blank title and correct metadata, and
that "open in tool" reproduces the original run's exact inputs. Walks
one representative save_as tool per hub (Profile, Content, Engagement,
Career): generate -> save -> find via search -> open in tool -> re-run
with the same inputs -- against the real service layer, the same way
every other tool golden test in this directory does (see conftest.py's
`rich_profile_user`, a plain DB user with no password, which is why
this exercises app.tools.service and app.workspace.assets directly
rather than through HTTP with a logged-in session).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.tools import service as tools_service
from app.tools.registry import get_tool
from app.workspace import assets as workspace_service

SAMPLE_RESUME = """\
Jamie Rivera
jamie.rivera@example.com

Experience
Senior Backend Engineer, Acme Corp
Jan 2020 - Present
- Led a team of eight engineers
- Reduced incident response time by half

Skills
Python, SQL
"""


@dataclass(frozen=True)
class _Case:
    hub: str
    tool_id: str
    raw_input: dict[str, object]
    expected_asset_type: str


_CASES = [
    _Case(
        hub="profile",
        tool_id="profile.headline_optimizer",
        raw_input={"target_role": "Staff Backend Engineer"},
        expected_asset_type="headline",
    ),
    _Case(
        hub="content",
        tool_id="content.post_generator",
        raw_input={"topic": "code review culture", "post_type": "insight"},
        expected_asset_type="post",
    ),
    _Case(
        hub="engagement",
        tool_id="engagement.comment_generator",
        raw_input={
            "post_text": "Unclear ownership is the real reason incidents drag on.",
            "angle": "I've led backend teams through this exact problem.",
            "stance": "agree_and_extend",
            "length": "medium",
        },
        expected_asset_type="comment",
    ),
    _Case(
        hub="career",
        tool_id="career.resume_analyzer",
        raw_input={"resume_text": SAMPLE_RESUME},
        expected_asset_type="analysis",
    ),
]


async def test_close_the_loop_across_every_hub(
    db_session: AsyncSession, rich_profile_user: User
) -> None:
    for case in _CASES:
        definition = get_tool(case.tool_id)
        assert definition.hub.value == case.hub

        # 1. Generate.
        run, _quota, _warning = await tools_service.run_tool(
            db_session, user=rich_profile_user, tool_id=case.tool_id, raw_input=case.raw_input
        )
        assert run.status == "succeeded"

        # 2. Save -- the frontend falls back to the tool's own name when
        # the user leaves the save title blank (ToolRunner.tsx's
        # `saveTitle.trim() || tool.name`), which is exactly the "useful
        # auto-generated title" this audits: never a blank or generic
        # "Untitled" string.
        marker = f"integration-marker-{case.tool_id.replace('.', '-')}"
        asset = await tools_service.save_run_as_asset(
            db_session,
            user=rich_profile_user,
            run_id=run.id,
            title=definition.name,
            body=f"{marker} -- real generated content for {definition.name}.",
            folder_id=None,
        )
        assert asset.type == case.expected_asset_type
        assert asset.title == definition.name
        assert asset.title.strip() != ""
        assert asset.source_tool_run_id == run.id

        # 3. Find via search.
        page = await workspace_service.list_assets(
            db_session, user_id=rich_profile_user.id, q=marker
        )
        assert [a.id for a in page.items] == [asset.id]
        found = page.items[0]
        assert found.source_tool_run_id is not None

        # 4. "Open in tool" -- fetch the run behind the found asset and
        # confirm its inputs are exactly the ones the original run was
        # actually recorded with (the full, schema-validated input,
        # defaults included -- not just the partial dict the caller
        # happened to submit).
        fetched_run = await tools_service.get_run_for_user(
            db_session, run_id=found.source_tool_run_id, user_id=rich_profile_user.id
        )
        assert fetched_run is not None
        assert fetched_run.tool_id == case.tool_id
        assert fetched_run.input == run.input
        for key, value in case.raw_input.items():
            assert fetched_run.input[key] == value

        # 5. Re-run with the reproduced inputs.
        rerun, _quota, _warning = await tools_service.run_tool(
            db_session, user=rich_profile_user, tool_id=case.tool_id, raw_input=fetched_run.input
        )
        assert rerun.status == "succeeded"
        assert rerun.id != run.id
