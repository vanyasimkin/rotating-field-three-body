import hashlib
import json
import re
import tomllib
from pathlib import Path


def test_release_versions_and_model_identity_are_consistent():
    root = Path(__file__).resolve().parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    version = project["project"]["version"]

    init_text = (root / "src/rotating_field_three_body/__init__.py").read_text(
        encoding="utf-8"
    )
    package_version = re.search(r'__version__ = "([^"]+)"', init_text).group(1)

    citation = (root / "CITATION.cff").read_text(encoding="utf-8")
    citation_version = re.search(r'^version: "([^"]+)"', citation, re.M).group(1)

    manifest = json.loads((root / "data/asset_manifest.json").read_text(encoding="utf-8"))
    model_info = json.loads(
        (root / "data/delta3_surrogate_corrected_model_info.json").read_text(
            encoding="utf-8"
        )
    )
    asset = manifest["assets"][0]

    assert version == package_version == citation_version == manifest["release_version"]
    assert asset["filename"] == "delta3_surrogate_corrected.joblib"
    assert asset["size_bytes"] == model_info["model_size_bytes"]
    assert asset["sha256"] == model_info["model_sha256"]


def test_pair_map_release_hash():
    root = Path(__file__).resolve().parents[1]
    path = root / "data/scm_pair_orientation_map_lmax6_beta2p5.npz"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == "a1e959250ee1af07af8ed16b90fb6f8c4c5c20b8a70c9c445d3134f0aa9d2a4d"
