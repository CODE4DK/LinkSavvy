"""Structured diff between two ProfileSnapshot versions.

Scalar fields (identity, about, metrics) are compared directly. List
fields (experiences, education, skills, certifications, languages,
projects) are matched by a stable key — never by list position, since
reordering a list should never look like every item changed — and
classified as added, removed, or modified.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.profiles.schema import ProfileSnapshot

_IDENTITY_FIELDS = [
    "full_name",
    "headline",
    "custom_url",
    "industry",
    "location",
    "profile_picture_url",
]
_METRICS_FIELDS = ["connections", "followers", "recommendations_received"]
_TOP_LEVEL_SCALAR_FIELDS = ["about"]


@dataclass(frozen=True)
class FieldChangeResult:
    path: str
    before: Any
    after: Any


@dataclass(frozen=True)
class ListItemChangeResult:
    key: str
    change: str  # 'added' | 'removed' | 'modified'
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    field_changes: list[FieldChangeResult] = field(default_factory=list)


@dataclass(frozen=True)
class DiffResult:
    field_changes: list[FieldChangeResult]
    list_changes: dict[str, list[ListItemChangeResult]]


def _experience_key(item: dict[str, Any]) -> str:
    start = item.get("start") or {}
    return f"{item.get('company') or ''} {item.get('title') or ''} {start.get('year') or ''}"


def _education_key(item: dict[str, Any]) -> str:
    return f"{item.get('school') or ''} {item.get('degree') or ''}"


def _name_key(item: dict[str, Any]) -> str:
    return item.get("name") or ""


def _certification_key(item: dict[str, Any]) -> str:
    return f"{item.get('name') or ''} {item.get('issuer') or ''}"


_LIST_KEY_FUNCS: dict[str, Callable[[dict[str, Any]], str]] = {
    "experiences": _experience_key,
    "education": _education_key,
    "skills": _name_key,
    "certifications": _certification_key,
    "languages": _name_key,
    "projects": _name_key,
}


def _diff_dict_fields(before: dict[str, Any], after: dict[str, Any]) -> list[FieldChangeResult]:
    changes = []
    for key in sorted(set(before) | set(after)):
        before_value, after_value = before.get(key), after.get(key)
        if before_value != after_value:
            changes.append(FieldChangeResult(path=key, before=before_value, after=after_value))
    return changes


def _diff_list(
    before_items: list[dict[str, Any]] | None,
    after_items: list[dict[str, Any]] | None,
    key_func: Callable[[dict[str, Any]], str],
) -> list[ListItemChangeResult]:
    before_by_key = {key_func(item): item for item in (before_items or [])}
    after_by_key = {key_func(item): item for item in (after_items or [])}

    changes: list[ListItemChangeResult] = []
    for key, before_item in before_by_key.items():
        if key not in after_by_key:
            changes.append(ListItemChangeResult(key=key, change="removed", before=before_item))
    for key, after_item in after_by_key.items():
        matching_before_item = before_by_key.get(key)
        if matching_before_item is None:
            changes.append(ListItemChangeResult(key=key, change="added", after=after_item))
        else:
            field_changes = _diff_dict_fields(matching_before_item, after_item)
            if field_changes:
                changes.append(
                    ListItemChangeResult(
                        key=key,
                        change="modified",
                        before=matching_before_item,
                        after=after_item,
                        field_changes=field_changes,
                    )
                )
    return changes


def diff_snapshots(before: ProfileSnapshot, after: ProfileSnapshot) -> DiffResult:
    before_dict = before.model_dump(mode="json")
    after_dict = after.model_dump(mode="json")

    field_changes: list[FieldChangeResult] = []
    for name in _TOP_LEVEL_SCALAR_FIELDS:
        if before_dict.get(name) != after_dict.get(name):
            field_changes.append(
                FieldChangeResult(
                    path=f"/{name}", before=before_dict.get(name), after=after_dict.get(name)
                )
            )

    before_identity = before_dict.get("identity") or {}
    after_identity = after_dict.get("identity") or {}
    for name in _IDENTITY_FIELDS:
        if before_identity.get(name) != after_identity.get(name):
            field_changes.append(
                FieldChangeResult(
                    path=f"/identity/{name}",
                    before=before_identity.get(name),
                    after=after_identity.get(name),
                )
            )

    before_metrics = before_dict.get("metrics") or {}
    after_metrics = after_dict.get("metrics") or {}
    for name in _METRICS_FIELDS:
        if before_metrics.get(name) != after_metrics.get(name):
            field_changes.append(
                FieldChangeResult(
                    path=f"/metrics/{name}",
                    before=before_metrics.get(name),
                    after=after_metrics.get(name),
                )
            )

    list_changes: dict[str, list[ListItemChangeResult]] = {}
    for list_name, key_func in _LIST_KEY_FUNCS.items():
        item_changes = _diff_list(before_dict.get(list_name), after_dict.get(list_name), key_func)
        if item_changes:
            list_changes[list_name] = item_changes

    return DiffResult(field_changes=field_changes, list_changes=list_changes)
