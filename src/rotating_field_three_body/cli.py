"""Command-line interface for model inference and one-triplet SCM calculations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .api import (
    compute_triplet_delta3_scm,
    predict_cluster_energy,
    predict_triplet_delta3,
)
from .assets import download_release_assets
from .config import DEFAULT_PARAMS
from .io import json_safe, read_centers, write_json
from .scm import SCMParams


def _emit(payload: Any, output: Path | None) -> None:
    if output is None:
        print(json.dumps(json_safe(payload), ensure_ascii=False, indent=2))
    else:
        write_json(output, payload)
        print(f"Saved: {output}")


def _params_from_args(args: argparse.Namespace) -> SCMParams:
    return SCMParams(
        eps1_r=args.eps1_r,
        eps2_r=args.eps2_r,
        a=args.radius,
        E0=args.field,
        eps0=DEFAULT_PARAMS.eps0,
        n_orient=args.n_orient,
        n_quad=args.n_quad,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rf3b",
        description="Rotating-field three-body SCM and ML3B utilities.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    triplet = subparsers.add_parser("predict-triplet", help="Predict one Delta3 value.")
    triplet.add_argument("--coordinates", type=Path, required=True)
    triplet.add_argument("--diameter", type=float, required=True)
    triplet.add_argument("--model", type=Path, required=True)
    triplet.add_argument("--no-domain-check", action="store_true")
    triplet.add_argument("--output", type=Path)

    cluster = subparsers.add_parser(
        "predict-cluster", help="Compute pair-only and pair-plus-ML3B energies."
    )
    cluster.add_argument("--coordinates", type=Path, required=True)
    cluster.add_argument("--diameter", type=float, required=True)
    cluster.add_argument("--model", type=Path, required=True)
    cluster.add_argument("--pair-map", type=Path, required=True)
    cluster.add_argument("--no-domain-check", action="store_true")
    cluster.add_argument("--output", type=Path)

    scm = subparsers.add_parser("scm-triplet", help="Run a direct matrix-SCM triplet.")
    scm.add_argument("--coordinates", type=Path, required=True)
    scm.add_argument("--pair-map", type=Path, required=True)
    scm.add_argument("--lmax", type=int, default=6)
    scm.add_argument("--n-quad", type=int, default=8000)
    scm.add_argument("--n-orient", type=int, default=8)
    scm.add_argument("--radius", type=float, default=1.0e-6)
    scm.add_argument("--field", type=float, default=1.0e5)
    scm.add_argument("--eps1-r", type=float, default=3.9)
    scm.add_argument("--eps2-r", type=float, default=81.0)
    scm.add_argument("--output", type=Path)

    assets = subparsers.add_parser("download-assets", help="Download verified assets.")
    assets.add_argument("--manifest", type=Path, required=True)
    assets.add_argument("--destination", type=Path, default=Path("data/external"))
    assets.add_argument("--name", action="append", dest="names")
    assets.add_argument("--overwrite", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "predict-triplet":
        result = predict_triplet_delta3(
            read_centers(args.coordinates),
            diameter=args.diameter,
            model=args.model,
            check_domain=not args.no_domain_check,
        )
        _emit(result, args.output)
        return 0

    if args.command == "predict-cluster":
        result = predict_cluster_energy(
            read_centers(args.coordinates),
            diameter=args.diameter,
            pair_map=args.pair_map,
            model=args.model,
            check_domain=not args.no_domain_check,
        )
        _emit(result, args.output)
        return 0

    if args.command == "scm-triplet":
        result = compute_triplet_delta3_scm(
            read_centers(args.coordinates),
            pair_map=args.pair_map,
            params=_params_from_args(args),
            lmax=args.lmax,
            n_quad=args.n_quad,
        )
        _emit(result, args.output)
        return 0

    if args.command == "download-assets":
        outputs = download_release_assets(
            args.destination,
            manifest=args.manifest,
            names=args.names,
            overwrite=args.overwrite,
        )
        for output in outputs:
            print(f"Verified: {output}")
        return 0

    raise RuntimeError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
