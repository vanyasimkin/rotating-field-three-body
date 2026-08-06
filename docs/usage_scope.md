# Supported use and validation scope

## Model use

Requires the trained Zenodo model and the included refined pair map.

```bash
python examples/predict_one_triplet.py --model data/external/delta3_surrogate_corrected.joblib
python examples/predict_cluster.py --model data/external/delta3_surrogate_corrected.joblib
```

## Direct SCM smoke test

```bash
python examples/run_one_scm_triplet.py --lmax 1 --n-quad 80
```

This verifies that the implementation runs at reduced resolution. It is not a publication calculation.

## One-geometry article-resolution calculation

```bash
rf3b scm-triplet \
  --coordinates data/triplet_example.json \
  --pair-map data/scm_pair_orientation_map_lmax6_beta2p5.npz \
  --lmax 6 \
  --n-quad 8000 \
  --n-orient 8 \
  --output outputs/triplet_scm.json
```

This command evaluates the supplied geometry with the declared numerical settings. It does not reproduce the article figures, tables, aggregate metrics, or full validation datasets, because those processed arrays and plotting scripts are outside the scope of this release.
