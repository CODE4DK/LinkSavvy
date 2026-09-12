#!/usr/bin/env python3
"""Guard the CLAUDE.md hard compliance rule in CI.

LinkSavvy must never scrape LinkedIn, parse LinkedIn HTML, drive a headless
browser against linkedin.com, or store LinkedIn credentials. The only
network calls permitted to LinkedIn are its official OAuth/API hosts, made
from apps/api/app/services/linkedin.py.

This script fails (non-zero exit) if any scanned source file:
  1. References a linkedin.com host outside that one allowlisted file.
  2. Imports a browser-automation library (selenium/playwright/puppeteer)
     outside a test file.
  3. Imports an HTML-scraping library (BeautifulSoup/bs4/cheerio).
  4. Contains a scraping-shaped identifier (scrape/scraper/crawl) outside a
     test file.

Run: python scripts/check_compliance.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SCAN_DIRS = [
    REPO_ROOT / "apps" / "api" / "app",
    REPO_ROOT / "apps" / "api" / "alembic",
    REPO_ROOT / "apps" / "web" / "src",
    REPO_ROOT / "packages" / "contracts" / "src",
]

SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx"}

# The only file allowed to reference a linkedin.com host: the official
# OAuth/API client. Nothing else may talk to LinkedIn.
LINKEDIN_HOST_ALLOWLIST = {
    REPO_ROOT / "apps" / "api" / "app" / "services" / "linkedin.py",
}

LINKEDIN_HOST_RE = re.compile(r"[a-z0-9.-]*linkedin\.com", re.IGNORECASE)
# Import-shaped only (python "import X" / "from X import", JS/TS "import
# ... from 'X'" / "require('X')") -- not any prose mention of the word.
# output_policy.py's own policy patterns legitimately name these libraries
# as strings to detect automation *instructions*, which isn't an import.
_AUTOMATION_LIBS = r"(selenium|playwright|pyppeteer|puppeteer)"
BROWSER_AUTOMATION_RE = re.compile(
    rf"\b(import|from)\b[^\n]{{0,40}}\b{_AUTOMATION_LIBS}\b"
    rf"|require\([^\n]{{0,20}}\b{_AUTOMATION_LIBS}\b",
    re.IGNORECASE,
)
_HTML_SCRAPING_LIBS = r"(beautifulsoup4?|bs4|cheerio)"
HTML_SCRAPING_IMPORT_RE = re.compile(
    rf"\b(import|from)\b[^\n]{{0,40}}\b{_HTML_SCRAPING_LIBS}\b"
    rf"|require\([^\n]{{0,20}}\b{_HTML_SCRAPING_LIBS}\b",
    re.IGNORECASE,
)
# Matches a *declaration* shaped like a scraping helper (function/class/
# variable/type named scrape-something), not the word appearing in prose --
# comments and UI copy legitimately say things like "never scraped".
SCRAPING_HELPER_RE = re.compile(
    r"\b(def|class|function|const|let|var|interface|type)\s+\w*"
    r"(scrape|scraper|scraping|crawl|crawler)\w*\b",
    re.IGNORECASE,
)

TEST_PATH_MARKERS = ("/tests/", "/test/", ".test.", ".spec.")


def is_test_file(path: Path) -> bool:
    normalized = "/" + str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    return path.name.startswith("test_") or any(marker in normalized for marker in TEST_PATH_MARKERS)


def iter_source_files() -> list[Path]:
    files = []
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
                continue
            if "node_modules" in path.parts or ".venv" in path.parts:
                continue
            files.append(path)
    return files


def check_file(path: Path, violations: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return

    rel = path.relative_to(REPO_ROOT)

    if LINKEDIN_HOST_RE.search(text) and path not in LINKEDIN_HOST_ALLOWLIST:
        violations.append(
            f"{rel}: references a linkedin.com host outside the allowlisted "
            "OAuth/API client (apps/api/app/services/linkedin.py)"
        )

    if BROWSER_AUTOMATION_RE.search(text) and not is_test_file(path):
        violations.append(
            f"{rel}: references a browser-automation library "
            "(selenium/playwright/puppeteer) outside a test file"
        )

    if HTML_SCRAPING_IMPORT_RE.search(text):
        violations.append(
            f"{rel}: references an HTML-scraping library (BeautifulSoup/bs4/cheerio) -- "
            "LinkSavvy must never parse LinkedIn HTML"
        )

    if SCRAPING_HELPER_RE.search(text) and not is_test_file(path):
        violations.append(
            f"{rel}: contains a scraping-shaped identifier (scrape/scraper/crawl) -- "
            "rename it, or remove it if it genuinely scrapes"
        )


def main() -> int:
    files = iter_source_files()
    violations: list[str] = []
    for path in files:
        check_file(path, violations)

    if violations:
        print("Compliance check FAILED (CLAUDE.md hard compliance rule):\n")
        for violation in violations:
            print(f"  - {violation}")
        print(f"\n{len(violations)} violation(s) across {len(files)} files scanned.")
        return 1

    print(f"Compliance check passed ({len(files)} files scanned).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
