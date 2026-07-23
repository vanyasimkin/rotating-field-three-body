# Created files

## New public package code

- `src/rotating_field_three_body/api.py`
- `src/rotating_field_three_body/assets.py`
- `src/rotating_field_three_body/io.py`
- `src/rotating_field_three_body/cli.py`
- `src/rotating_field_three_body/config.py`
- `src/rotating_field_three_body/__init__.py`
- `src/rotating_field_three_body/__main__.py`

## Verified existing numerical code packaged under importable names

- `scm_core.py` -> `src/rotating_field_three_body/scm.py`
- `scm3d_geometry.py` -> `src/rotating_field_three_body/geometry.py`
- `scm3d_pair_physical.py` -> `src/rotating_field_three_body/pair_map.py`
- `delta3_invariant_features.py` -> `src/rotating_field_three_body/features.py`
- `delta3_surrogate_runtime.py` -> `src/rotating_field_three_body/surrogate.py`
- `cluster_motifs.py` -> `src/rotating_field_three_body/motifs.py`

The original versions are preserved in `source_backup/`.

## Repository infrastructure

- `pyproject.toml`, `.gitignore`, `LICENSE`, `CITATION.cff`
- `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`
- `.github/workflows/ci.yml`
- `tools/import_existing_project_files.ps1`
- `tools/create_github_repo.ps1`
- `tools/verify_release.py`
- examples, tests, documentation, asset manifest template, and sample coordinate files

## Expected results

- editable installation through `pip install -e .`;
- CLI command `rf3b`;
- direct SCM triplet calculation;
- actual surrogate inference after the canonical model is downloaded;
- pair-only and pair-plus-ML3B cluster output;
- CI compilation and tests on pushes and pull requests.
