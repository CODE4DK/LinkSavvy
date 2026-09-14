"""MySQL FULLTEXT boolean-mode search for assets, with a LIKE-based
fallback for SQLite (the test database has no FULLTEXT index at all).
True boolean-mode relevance behavior can only be verified against real
MySQL -- see docs/adr/0009, the same category of environment limitation
recorded for every prior phase's `alembic upgrade`/`downgrade` check.
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import Select, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset

_WORD_RE = re.compile(r"[\w-]+")


def boolean_mode_query(q: str) -> str:
    """Every word becomes a required prefix match (`+word*`) -- a search
    for "backend reliability" only matches assets containing something
    starting with both "backend" and "reliability", ranked by MySQL's
    own relevance score rather than by recency."""
    words = _WORD_RE.findall(q)
    return " ".join(f"+{word}*" for word in words) or q


def apply_search(stmt: Select[Any], *, db: AsyncSession, q: str) -> Select[Any]:
    dialect = db.get_bind().dialect.name
    if dialect == "mysql":
        where_clause = text("MATCH(assets.title, assets.body) AGAINST (:search_q IN BOOLEAN MODE)")
        order_clause = text(
            "MATCH(assets.title, assets.body) AGAINST (:search_q IN BOOLEAN MODE) DESC"
        )
        return (
            stmt.where(where_clause).order_by(order_clause).params(search_q=boolean_mode_query(q))
        )
    like = f"%{q}%"
    return stmt.where(or_(Asset.title.ilike(like), Asset.body.ilike(like))).order_by(
        Asset.created_at.desc()
    )
