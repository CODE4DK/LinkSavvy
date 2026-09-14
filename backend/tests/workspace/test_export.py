from __future__ import annotations

import uuid
import zipfile
from io import BytesIO

from app.models.asset import Asset
from app.workspace.export import export_asset, export_assets_zip


def _asset(title: str = "My Post", body: str = "Line one.\nLine two.") -> Asset:
    return Asset(
        user_id=uuid.uuid4(),
        type="post",
        title=title,
        body=body,
        body_format="text",
    )


def test_export_txt_contains_title_and_body() -> None:
    content = export_asset(_asset(), fmt="txt").decode()
    assert "My Post" in content
    assert "Line one." in content


def test_export_md_uses_a_heading() -> None:
    content = export_asset(_asset(), fmt="md").decode()
    assert content.startswith("# My Post")


def test_export_pdf_produces_pdf_bytes() -> None:
    content = export_asset(_asset(), fmt="pdf")
    assert content.startswith(b"%PDF")


def test_export_docx_produces_a_valid_zip_container() -> None:
    content = export_asset(_asset(), fmt="docx")
    with zipfile.ZipFile(BytesIO(content)) as zf:
        assert "word/document.xml" in zf.namelist()


def test_export_unsupported_format_raises() -> None:
    try:
        export_asset(_asset(), fmt="rtf")
        raise AssertionError("expected a ValueError")
    except ValueError:
        pass


def test_export_assets_zip_bundles_every_asset_with_unique_names() -> None:
    assets = [_asset(title="Same Title"), _asset(title="Same Title")]
    content = export_assets_zip(assets, fmt="txt")
    with zipfile.ZipFile(BytesIO(content)) as zf:
        names = zf.namelist()
        assert len(names) == 2
        assert len(set(names)) == 2
