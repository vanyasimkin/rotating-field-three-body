#!/usr/bin/env python3
"""Run lightweight repository checks and write a JSON verification report."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], cwd: Path) -> dict:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("reports/release_verification.json"))
    args = parser.parse_args()
    root = args.root.resolve()

    checks = [
        run([sys.executable, "-m", "compileall", "-q", "src", "examples", "tests"], root),
        run([sys.executable, "-m", "pytest", "-q"], root),
        run([sys.executable, "-m", "rotating_field_three_body", "--help"], root),
    ]

    tracked = [
        root / "data" / "scm_pair_orientation_map_lmax6_beta2p5.npz",
        root / "data" / "delta3_surrogate_corrected_model_info.json",
        root / "data" / "delta3_surrogate_corrected_metrics.json",
    ]
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
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
        "passed": all(check["passed"] for check in checks),
        "limitations": [
            "The canonical trained joblib model is not included in this starter package.",
            "The SCM smoke output uses reduced numerical settings and is not a publication result.",
            "Research step scripts must be imported from the user's current project snapshot.",
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
