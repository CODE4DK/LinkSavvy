"""Fails if a shipped prompt's body changed without its version bumping.

`app/ai/prompts/prompts.lock.json` is the committed baseline: for every
prompt id it records the version and body hash last reviewed. If someone
edits a prompt body and forgets to bump `version` (and regenerate the
lockfile), this test catches it — the whole point of prompt versioning is
that a cache entry or an in-flight integration pinned to version N can
trust that version N's meaning never moves out from under it.
"""

from __future__ import annotations

from app.ai.prompts.lockfile import compute_lockfile, read_lockfile


def test_lockfile_matches_current_prompt_bodies() -> None:
    current = compute_lockfile()
    committed = read_lockfile()

    assert committed, (
        "prompts.lock.json is empty or missing — run "
        "`uv run python -m app.ai.prompts.lockfile --write` and commit the result"
    )

    missing_from_lockfile = current.keys() - committed.keys()
    assert not missing_from_lockfile, (
        f"prompt(s) {sorted(missing_from_lockfile)} aren't in prompts.lock.json — "
        "run `uv run python -m app.ai.prompts.lockfile --write` and commit the result"
    )

    stale = {
        prompt_id: (committed[prompt_id], current[prompt_id])
        for prompt_id in current
        if committed.get(prompt_id) != current[prompt_id]
    }
    assert not stale, (
        "prompt body/version drifted from prompts.lock.json for: "
        f"{stale} — if this was an intentional edit, bump `version` in the prompt's "
        "frontmatter, then run `uv run python -m app.ai.prompts.lockfile --write` "
        "and commit the updated lockfile"
    )
