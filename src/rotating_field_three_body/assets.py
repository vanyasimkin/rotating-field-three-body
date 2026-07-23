"""Download and verify externally hosted model/data assets."""

from __future__ import annotations

import hashlib
import json
import shutil
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable


def sha256_file(path: Path | str, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def load_asset_manifest(path: Path | str) -> Dict[str, Any]:
    manifest_path = Path(path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("assets"), list):
        raise ValueError("Asset manifest must contain a list field named 'assets'.")
    return payload


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "rotating-field-three-body-assets/1.0"},
    )
    try:
        with urllib.request.urlopen(request) as response, temporary.open("wb") as out:
            shutil.copyfileobj(response, out, length=8 * 1024 * 1024)
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def download_release_assets(
    destination: Path | str,
    *,
    manifest: Path | str,
    names: Iterable[str] | None = None,
    overwrite: bool = False,
) -> list[Path]:
    """Download selected assets and verify declared SHA-256 hashes.

    Empty or placeholder URLs are rejected deliberately. Fill the manifest only
    after the Zenodo records or another immutable public archive exist.
    """
    destination = Path(destination)
    payload = load_asset_manifest(manifest)
    selected = None if names is None else set(names)
    outputs: list[Path] = []

    for item in payload["assets"]:
        name = str(item["name"])
        if selected is not None and name not in selected:
            continue
        filename = str(item["filename"])
        url = str(item.get("url") or "").strip()
        expected = str(item.get("sha256") or "").strip().lower()
        if not url or "REPLACE_" in url:
            raise ValueError(
                f"Asset {name!r} has no public URL yet. Update the manifest "
                "after the Zenodo record is created."
            )
        if len(expected) != 64:
            raise ValueError(f"Asset {name!r} has an invalid SHA-256 value.")

        output = destination / filename
        if output.exists() and not overwrite:
            actual = sha256_file(output)
            if actual == expected:
                outputs.append(output)
                continue
            raise FileExistsError(
                f"Existing file {output} has SHA-256 {actual}, expected {expected}. "
                "Use overwrite=True to replace it."
            )

        _download(url, output)
        actual = sha256_file(output)
        if actual != expected:
            output.unlink(missing_ok=True)
            raise RuntimeError(
                f"SHA-256 mismatch for {name}: downloaded {actual}, expected {expected}."
            )
        outputs.append(output)

    if selected is not None:
        found = {str(item["name"]) for item in payload["assets"]}
        missing = selected.difference(found)
        if missing:
            raise KeyError(f"Unknown assets requested: {sorted(missing)}")
    return outputs
