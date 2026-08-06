"""Small JSON/CSV I/O helpers for examples and the command-line interface."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


def read_centers(path: Path | str) -> np.ndarray:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        data = payload.get("centers", payload) if isinstance(payload, dict) else payload
        centers = np.asarray(data, dtype=float)
    elif suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        required = {"x", "y", "z"}
        if not rows or not required.issubset(rows[0]):
            raise ValueError("CSV must contain columns x,y,z.")
        centers = np.asarray(
            [[float(row["x"]), float(row["y"]), float(row["z"])] for row in rows],
            dtype=float,
        )
    else:
        raise ValueError("Coordinates must be supplied as .json or .csv.")
    if centers.ndim != 2 or centers.shape[1] != 3:
        raise ValueError(f"Coordinates must have shape (N, 3), got {centers.shape}.")
    if not np.all(np.isfinite(centers)):
        raise ValueError("Coordinates contain NaN or infinite values.")
    return centers


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value


def write_json(path: Path | str, payload: Any) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(json_safe(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
