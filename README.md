# Rotating-Field Three-Body Polarization

[![CI](https://github.com/vanyasimkin/rotating-field-three-body/actions/workflows/ci.yml/badge.svg)](https://github.com/vanyasimkin/rotating-field-three-body/actions/workflows/ci.yml)
[![Model DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21512150.svg)](https://doi.org/10.5281/zenodo.21512150)

Matrix self-consistent multipole (SCM) calculations and a permutation-invariant ML3B surrogate for dielectric colloids in an electric field rotating in the `xy` plane.

## Scope

This repository provides:

- the matrix-SCM implementation used for fixed-geometry calculations;
- the three-dimensional triplet geometry convention;
- the physically constrained SCM pair-map interpolator;
- the 120-feature permutation-invariant representation;
- runtime tools for the released ML3B surrogate;
- high-level Python and command-line interfaces;
- examples, unit tests, and continuous integration.

The trained model is archived separately in Zenodo because the joblib file is 5.77 GB. The refined pair-interaction map and model metadata are included in this repository.

This GitHub repository is the maintained software and model-use release.

The numerical datasets and publication analysis/plotting scripts underlying the figures, tables, and quantitative results of the accompanying article are archived separately on Zenodo:

**Article dataset:** https://doi.org/10.5281/zenodo.21873974

The trained ML3B surrogate and its archived model metadata are available at:

**ML3B model archive:** https://doi.org/10.5281/zenodo.21512150

## Released model

Zenodo DOI: `10.5281/zenodo.21512150`

```text
delta3_surrogate_corrected.joblib
size:   5,767,044,032 bytes
SHA256: 75f58bd77a49b4dce61ffcfe2591f5183bdfc709e9dd25a1f2a2f9d7d42eed68
```

The saved estimator was produced with Python 3.13.3, NumPy 2.3.3, scikit-learn 1.7.2, and joblib 1.5.2. Model inference is verified only in that recorded environment until additional environments are explicitly tested. Source-level CI covers Python 3.11 and 3.13.

> **Security:** joblib files use Python pickle semantics and can execute code while loading. Download the model only from the DOI above and verify its SHA-256 before calling `joblib.load`. See [SECURITY.md](SECURITY.md).

## Installation

```bash
git clone https://github.com/vanyasimkin/rotating-field-three-body.git
cd rotating-field-three-body

python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate

python -m pip install --upgrade pip
```

For the closest match to the archived model environment, use Python 3.13 and the dependency versions recorded in `data/delta3_surrogate_corrected_model_info.json`.

## Download and verify the model

The trained model is required for ML3B predictions. Download and verify
the archived model with:

```bash
rf3b download-assets \
  --manifest data/asset_manifest.json \
  --destination data/external
```
The 5.77 GB model is not required for the direct SCM examples.

The downloader writes through a temporary `.part` file and verifies both the declared file size and SHA-256 checksum before accepting the asset.

## Predict one triplet

Coordinates and particle diameter must use the same length unit. The released model predicts the irreducible three-body energy for the fixed physical parameters and normalization used during training.

```bash
rf3b predict-triplet \
  --coordinates data/triplet_example.json \
  --diameter 2e-6 \
  --model data/external/delta3_surrogate_corrected.joblib \
  --output outputs/triplet_prediction.json
```

Python API:

```python
from rotating_field_three_body import predict_triplet_delta3
from rotating_field_three_body.io import read_centers

result = predict_triplet_delta3(
    read_centers("data/triplet_example.json"),
    diameter=2.0e-6,
    model="data/external/delta3_surrogate_corrected.joblib",
)
print(result["delta3_J"], result["inside_training_domain"])
```

## Predict a cluster

```bash
rf3b predict-cluster \
  --coordinates data/cluster_example.json \
  --diameter 2e-6 \
  --pair-map data/scm_pair_orientation_map_lmax6_beta2p5.npz \
  --model data/external/delta3_surrogate_corrected.joblib \
  --output outputs/cluster_prediction.json
```

The reported `pair_plus_ml3b` energy is a truncated pair-plus-three-body expansion. It is not the direct full-cluster SCM energy and omits irreducible contributions of order four and above.

## Direct SCM triplet

Reduced-resolution software smoke test:

```bash
python examples/run_one_scm_triplet.py --lmax 1 --n-quad 80
```

Article-resolution settings for one supplied geometry:

```bash
rf3b scm-triplet \
  --coordinates data/triplet_example.json \
  --pair-map data/scm_pair_orientation_map_lmax6_beta2p5.npz \
  --lmax 6 \
  --n-quad 8000 \
  --n-orient 8 \
  --output outputs/triplet_scm.json
```

Reduced smoke-test outputs must not be substituted for article values.

## Coordinate convention

A reference triplet is defined by

```text
r1 = (0, 0, 0)
r2 = r12 (cos(alpha), sin(alpha), 0)
r3 = r13 (cos(alpha + gamma), sin(alpha + gamma), 0)
```

and then tilted around the laboratory `x` axis by `psi`.

- `gamma`: internal angle between `r12` and `r13`;
- `alpha`: azimuthal orientation before tilt;
- `psi`: tilt of the triangle plane relative to the field-rotation plane.

## Scientific interpretation

- **Defined within the model:** SCM equations, pair subtraction, feature construction, and the pair-plus-three-body truncation.
- **Numerical observations:** computed energies, validation metrics, runtimes, and boundary locations for declared parameters and artifacts.
- **Interpretations:** implications for motif selection and self-assembly; these are not guarantees of the software API.

See [MODEL_CARD.md](MODEL_CARD.md) and [docs/interpretation_scope.md](docs/interpretation_scope.md).

## Citation

For model use, cite the Zenodo model record and the specific GitHub release/tag. The accompanying journal article should be cited once its bibliographic record is available. Citation metadata are provided in [CITATION.cff](CITATION.cff).

## Licenses

- Source code in this repository: BSD 3-Clause License, see [LICENSE](LICENSE).
- Files in the associated Zenodo model record: Creative Commons Attribution 4.0 International, as stated on that record.
