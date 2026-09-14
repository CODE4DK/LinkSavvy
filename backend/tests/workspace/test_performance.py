"""B4: seeds 5,000 assets for one user and asserts a Workspace search
comes back fast. A bulk Core `insert()` is used instead of 5,000
individual ORM `add()`/`commit()` calls -- the point here is measuring
`list_assets` itself, not paying an unrelated insertion tax first.

The frontend's own virtualization (VirtualRows) is exercised by its own
component test in frontend -- this file is the backend half: search
latency at Workspace's stated scale. See docs/adr/0009 for the index
review this motivated.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from app.models.asset import Asset
from app.models.user import User
from app.workspace import assets as service

ASSET_COUNT = 5000
SEARCH_BUDGET_SECONDS = 0.5


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"perf-{uuid.uuid4()}@example.com", full_name="Perf Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _seed_assets(db: AsyncSession, *, user_id: uuid.UUID, count: int) -> None:
    rows: list[dict[str, Any]] = [
        {
            "id": uuid7(),
            "user_id": user_id,
            "type": "post",
            "title": f"Post number {i}" if i != count // 2 else "Backend reliability deep dive",
            "body": (
                "Just another saved post about career growth."
                if i != count // 2
                else "A detailed post about backend reliability and on-call practices."
            ),
            "body_format": "text",
            "metadata": {},
            "tags": [],
            "is_favourite": False,
        }
        for i in range(count)
    ]
    await db.execute(insert(Asset), rows)
    await db.commit()


async def test_search_is_fast_at_five_thousand_assets(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _seed_assets(db_session, user_id=user.id, count=ASSET_COUNT)

    started = time.perf_counter()
    page = await service.list_assets(db_session, user_id=user.id, q="reliability")
    elapsed = time.perf_counter() - started

    assert [a.title for a in page.items] == ["Backend reliability deep dive"]
    assert (
        elapsed < SEARCH_BUDGET_SECONDS
    ), f"search took {elapsed:.3f}s, budget is {SEARCH_BUDGET_SECONDS}s"


async def test_unfiltered_listing_is_fast_at_five_thousand_assets(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _seed_assets(db_session, user_id=user.id, count=ASSET_COUNT)

    started = time.perf_counter()
    page = await service.list_assets(db_session, user_id=user.id, limit=25)
    elapsed = time.perf_counter() - started

    assert len(page.items) == 25
    assert page.next_cursor is not None
    assert (
        elapsed < SEARCH_BUDGET_SECONDS
    ), f"listing took {elapsed:.3f}s, budget is {SEARCH_BUDGET_SECONDS}s"
