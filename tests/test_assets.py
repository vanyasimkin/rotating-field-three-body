import hashlib
import json
from pathlib import Path

import pytest

from rotating_field_three_body.assets import (
    download_release_assets,
    load_asset_manifest,
)


def _manifest(path: Path, *, filename: str, size: int, sha256: str) -> Path:
    payload = {
        "schema_version": 1,
        "assets": [
            {
                "name": "example",
                "filename": filename,
                "url": "https://example.org/example.bin",
                "sha256": sha256,
                "size_bytes": size,
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_existing_asset_is_reused_only_after_size_and_hash_check(tmp_path):
    content = b"verified asset"
    expected = hashlib.sha256(content).hexdigest()
    manifest = _manifest(
        tmp_path / "manifest.json",
        filename="example.bin",
        size=len(content),
        sha256=expected,
    )
    destination = tmp_path / "external"
    destination.mkdir()
    output = destination / "example.bin"
    output.write_bytes(content)

    files = download_release_assets(destination, manifest=manifest)
    assert files == [output]


def test_manifest_rejects_path_traversal(tmp_path):
    manifest = _manifest(
        tmp_path / "manifest.json",
        filename="../example.bin",
        size=1,
        sha256="0" * 64,
    )
    with pytest.raises(ValueError, match="plain filename"):
        load_asset_manifest(manifest)


def test_unknown_asset_is_rejected_before_download(tmp_path):
    manifest = _manifest(
        tmp_path / "manifest.json",
        filename="example.bin",
        size=1,
        sha256="0" * 64,
    )
    with pytest.raises(KeyError, match="Unknown assets"):
        download_release_assets(tmp_path / "external", manifest=manifest, names=["missing"])
