"""Guards against editing a prompt's meaning without bumping its version.

`prompts.lock.json` records, for every prompt id, the version and body
hash committed last. `tests/ai/test_prompt_lockfile.py` recomputes the
current hashes and fails if a prompt's body changed while its version
frontmatter field stayed the same — the only legitimate way to change a
prompt's wording is to bump `version` and regenerate this file in the
same commit.

Regenerate after an intentional change:
    uv run python -m app.ai.prompts.lockfile --write
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.ai.prompts.loader import DEFAULT_PROMPTS_DIR, PromptRegistry

LOCKFILE_PATH = DEFAULT_PROMPTS_DIR / "prompts.lock.json"


def compute_lockfile(prompts_dir: Path = DEFAULT_PROMPTS_DIR) -> dict[str, dict[str, object]]:
    registry = PromptRegistry(prompts_dir)
    return {
        template.id: {"version": template.version, "body_sha256": template.body_hash}
        for template in registry.all()
    }


def read_lockfile(path: Path = LOCKFILE_PATH) -> dict[str, dict[str, object]]:
    if not path.is_file():
        return {}
    result: dict[str, dict[str, object]] = json.loads(path.read_text())
    return result


def write_lockfile(path: Path = LOCKFILE_PATH) -> None:
    lockfile = compute_lockfile()
    path.write_text(json.dumps(lockfile, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    if "--write" in sys.argv:
        write_lockfile()
        print(f"wrote {LOCKFILE_PATH}")
    else:
        print(json.dumps(compute_lockfile(), indent=2, sort_keys=True))
