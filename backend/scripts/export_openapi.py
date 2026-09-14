"""Dump the FastAPI app's OpenAPI schema for the frontend's contracts codegen."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "frontend" / "openapi.json"


def main() -> None:
    schema = app.openapi()
    OUTPUT_PATH.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
