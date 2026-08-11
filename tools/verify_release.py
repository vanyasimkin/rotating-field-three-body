#!/usr/bin/env python3
"""Run release checks and write a machine-readable verification report."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_MODEL_NAME = "delta3_surrogate_corrected.joblib"
EXPECTED_MODEL_SIZE = 5_767_044_032
EXPECTED_MODEL_SHA256 = (
    "75f58bd77a49b4dce61ffcfe2591f5183bdfc709e9dd25a1f2a2f9d7d42eed68"
)
FORBIDDEN_DIRS = {"source_backup", "reports"}
FORBIDDEN_NAMES = {
    "make_prl_figures_main.py",
    "make_prl_figures_supplementary.py",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], cwd: Path, *, env: dict[str, str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }


def check_versions(root: Path) -> dict[str, Any]:
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    pyproject_version = project["project"]["version"]

    init_text = (root / "src/rotating_field_three_body/__init__.py").read_text(
        encoding="utf-8"
    )
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', init_text, re.M)
    init_version = match.group(1) if match else None

    citation_text = (root / "CITATION.cff").read_text(encoding="utf-8")
    match = re.search(r'^version:\s*["\']?([^"\'\s]+)', citation_text, re.M)
    citation_version = match.group(1) if match else None

    manifest = json.loads((root / "data/asset_manifest.json").read_text(encoding="utf-8"))
    manifest_version = manifest.get("release_version")
    versions = {
        "pyproject": pyproject_version,
        "package": init_version,
        "citation": citation_version,
        "asset_manifest": manifest_version,
    }
    return {
        "name": "version_consistency",
        "versions": versions,
        "passed": len(set(versions.values())) == 1 and None not in versions.values(),
    }


def check_repository_scope(root: Path) -> dict[str, Any]:
    violations: list[str] = []
    ignored_roots = {"outputs", "data/external", ".venv", "build", "dist", "wheelhouse"}
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if any(relative == item or relative.startswith(item + "/") for item in ignored_roots):
            continue
        if path.is_dir() and relative in FORBIDDEN_DIRS:
            violations.append(relative + "/")
        if path.is_file():
            if path.suffix.lower() == ".joblib":
                violations.append(relative)
            if path.name in FORBIDDEN_NAMES:
                violations.append(relative)
            if path.stat().st_size > 100_000_000:
                violations.append(f"{relative} (>100 MB)")
    return {
        "name": "public_release_scope",
        "violations": sorted(set(violations)),
        "passed": not violations,
    }


def check_manifest(root: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    code = (
        "from rotating_field_three_body.assets import load_asset_manifest; "
        "m=load_asset_manifest('data/asset_manifest.json'); "
        "a=m['assets'][0]; "
        f"assert a['filename']=='{EXPECTED_MODEL_NAME}'; "
        f"assert a['size_bytes']=={EXPECTED_MODEL_SIZE}; "
        f"assert a['sha256']=='{EXPECTED_MODEL_SHA256}'"
    )
    result = run([sys.executable, "-c", code], root, env=env)
    result["name"] = "asset_manifest"
    return result


def check_model(root: Path, model_path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": "real_model_inference",
        "path": str(model_path),
        "passed": False,
    }
    if not model_path.exists():
        result["error"] = "model file does not exist"
        return result
    result["size_bytes"] = model_path.stat().st_size
    result["sha256"] = sha256(model_path)
    if result["size_bytes"] != EXPECTED_MODEL_SIZE:
        result["error"] = "model size mismatch"
        return result
    if result["sha256"] != EXPECTED_MODEL_SHA256:
        result["error"] = "model SHA-256 mismatch"
        return result

    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    code = f"""
from rotating_field_three_body import predict_triplet_delta3
from rotating_field_three_body.io import read_centers
result = predict_triplet_delta3(
    read_centers(r'{(root / 'data/triplet_example.json').as_posix()}'),
    diameter=2.0e-6,
    model=r'{model_path.as_posix()}',
)
assert isinstance(result['delta3_J'], float)
assert result['inside_training_domain'] in (True, False)
print(result['delta3_J'])
"""
    inference = run([sys.executable, "-c", code], root, env=env)
    result["inference"] = inference
    result["passed"] = inference["passed"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--model", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/release_verification.json")
    )
    args = parser.parse_args()
    root = args.root.resolve()

    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    wheel_dir = root / "outputs" / "wheelhouse"
    wheel_dir.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = [
        run(
            [sys.executable, "-m", "compileall", "-q", "src", "examples", "tests", "tools"],
            root,
            env=env,
        ),
        run([sys.executable, "-m", "pytest", "-q"], root, env=env),
        run([sys.executable, "-m", "rotating_field_three_body", "--help"], root, env=env),
        run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                ".",
                "--no-deps",
                "--wheel-dir",
                str(wheel_dir),
            ],
            root,
            env=env,
        ),
        check_versions(root),
        check_repository_scope(root),
        check_manifest(root),
    ]

    if args.model is not None:
        checks.append(check_model(root, args.model.resolve()))

    tracked = [
        root / "data/scm_pair_orientation_map_lmax6_beta2p5.npz",
        root / "data/delta3_surrogate_corrected_model_info.json",
        root / "data/delta3_surrogate_corrected_metrics.json",
        root / "data/asset_manifest.json",
    ]
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "python": sys.version,
        "checks": checks,
        "files": [
            {
                "path": str(path.relative_to(root)),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in tracked
            if path.exists()
        ],
        "passed": all(check.get("passed", False) for check in checks),
        "model_inference_executed": args.model is not None,
        "limitations": [
            "The article figure/table arrays and plotting scripts are outside this release.",
            "Reduced SCM smoke tests are software checks, not publication results.",
            "A full model inference check is performed only when --model is supplied.",
        ],
    }
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {output}")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
