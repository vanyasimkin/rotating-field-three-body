# Release checklist for v0.1.0

## Zenodo

- [ ] All seven Zenodo files show `completed`.
- [ ] Publication date equals the actual publication date.
- [ ] Creator order matches the agreed author order.
- [ ] Version is `0.1.0`.
- [ ] DOI is `10.5281/zenodo.21512150`.
- [ ] Record and files are public.
- [ ] The description explicitly states that figure/table datasets and plotting scripts are not included.
- [ ] The record is published before the final GitHub release is tagged.

## Repository metadata

- [ ] `pyproject.toml`, `src/rotating_field_three_body/__init__.py`, `CITATION.cff`, and `data/asset_manifest.json` all use version `0.1.0`.
- [ ] README, model card, and Zenodo use the same model filename, size, and SHA-256.
- [ ] No `.joblib`, `data/external/`, `outputs/`, `source_backup/`, or article plotting scripts are tracked.

## Verification

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python tools/verify_release.py
rf3b download-assets --manifest data/asset_manifest.json --destination data/external
python tools/verify_release.py --model data/external/delta3_surrogate_corrected.joblib
```

- [ ] Unit tests pass.
- [ ] Wheel builds.
- [ ] CLI help works.
- [ ] Downloaded model size and SHA-256 match.
- [ ] The real model loads in the recorded environment.
- [ ] One-triplet inference smoke test completes.

## GitHub release

```bash
git add -A
git commit -m "Prepare public v0.1.0 model-use release"
git tag -a v0.1.0 -m "Rotating-field three-body model-use release v0.1.0"
git push origin main
git push origin v0.1.0
```

Create a GitHub release from tag `v0.1.0` using `release_notes_v0.1.0.md`.
