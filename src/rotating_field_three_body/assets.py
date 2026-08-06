"""Download and verify externally hosted model assets."""

from __future__ import annotations

import hashlib
import json
import shutil
import string
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping
from urllib.parse import urlparse

_HEX_DIGITS = set(string.hexdigits)


def sha256_file(path: Path | str, chunk_size: int = 8 * 1024 * 1024) -> str:
    """Return the lowercase SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _validated_asset(item: Mapping[str, Any], *, index: int) -> Dict[str, Any]:
    if not isinstance(item, Mapping):
        raise ValueError(f"Asset entry {index} must be a JSON object.")

    name = str(item.get("name") or "").strip()
    filename = str(item.get("filename") or "").strip()
    url = str(item.get("url") or "").strip()
    sha256 = str(item.get("sha256") or "").strip().lower()
    size = item.get("size_bytes")

    if not name:
        raise ValueError(f"Asset entry {index} has no name.")
    if not filename or Path(filename).name != filename or filename in {".", ".."}:
        raise ValueError(
            f"Asset {name!r} must use a plain filename without directories."
        )
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"Asset {name!r} must use an absolute HTTPS URL.")
    if len(sha256) != 64 or any(char not in _HEX_DIGITS for char in sha256):
        raise ValueError(f"Asset {name!r} has an invalid SHA-256 value.")
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise ValueError(f"Asset {name!r} must declare a positive integer size_bytes.")

    output = dict(item)
    output.update(
        {
            "name": name,
            "filename": filename,
            "url": url,
            "sha256": sha256,
            "size_bytes": size,
        }
    )
    return output


def load_asset_manifest(path: Path | str) -> Dict[str, Any]:
    """Load and validate a release asset manifest."""
    manifest_path = Path(path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Asset manifest root must be a JSON object.")
    if payload.get("schema_version") != 1:
        raise ValueError("Only asset-manifest schema_version 1 is supported.")
    raw_assets = payload.get("assets")
    if not isinstance(raw_assets, list) or not raw_assets:
        raise ValueError("Asset manifest must contain a non-empty list named 'assets'.")

    assets = [_validated_asset(item, index=index) for index, item in enumerate(raw_assets)]
    names = [item["name"] for item in assets]
    filenames = [item["filename"] for item in assets]
    if len(names) != len(set(names)):
        raise ValueError("Asset names must be unique.")
    if len(filenames) != len(set(filenames)):
        raise ValueError("Asset filenames must be unique.")

    output = dict(payload)
    output["assets"] = assets
    return output


def _download(url: str, destination: Path, *, timeout: float = 120.0) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "rotating-field-three-body-assets/0.1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response, temporary.open(
            "wb"
        ) as out:
            shutil.copyfileobj(response, out, length=8 * 1024 * 1024)
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _verify_file(path: Path, *, expected_sha256: str, expected_size: int) -> None:
    actual_size = path.stat().st_size
    if actual_size != expected_size:
        raise RuntimeError(
            f"Size mismatch for {path.name}: downloaded {actual_size} bytes, "
            f"expected {expected_size}."
        )
    actual_sha256 = sha256_file(path)
    if actual_sha256 != expected_sha256:
        raise RuntimeError(
            f"SHA-256 mismatch for {path.name}: downloaded {actual_sha256}, "
            f"expected {expected_sha256}."
        )


def download_release_assets(
    destination: Path | str,
    *,
    manifest: Path | str,
    names: Iterable[str] | None = None,
    overwrite: bool = False,
) -> list[Path]:
    """Download selected assets and verify their size and SHA-256.

    The function accepts only manifest-declared HTTPS URLs and plain output
    filenames. Existing files are reused only when both their declared size and
    SHA-256 match.
    """
    destination = Path(destination)
    payload = load_asset_manifest(manifest)
    available = {str(item["name"]): item for item in payload["assets"]}
    selected = list(available) if names is None else list(dict.fromkeys(names))
    missing = set(selected).difference(available)
    if missing:
        raise KeyError(f"Unknown assets requested: {sorted(missing)}")

    outputs: list[Path] = []
    for name in selected:
        item = available[name]
        output = destination / item["filename"]
        if output.exists() and not overwrite:
            try:
                _verify_file(
                    output,
                    expected_sha256=item["sha256"],
                    expected_size=item["size_bytes"],
                )
            except RuntimeError as error:
                raise FileExistsError(
                    f"Existing file {output} does not match the release manifest. "
                    "Use overwrite=True to replace it."
                ) from error
            outputs.append(output)
            continue

        _download(item["url"], output)
        try:
            _verify_file(
                output,
                expected_sha256=item["sha256"],
                expected_size=item["size_bytes"],
            )
        except Exception:
            output.unlink(missing_ok=True)
            raise
        outputs.append(output)
    return outputs
