# Reproduction levels

## Level 1: model use

Requires the trained model and the included refined pair map.

```bash
python examples/predict_one_triplet.py --model data/external/delta3_surrogate_corrected.joblib
python examples/predict_cluster.py --model data/external/delta3_surrogate_corrected.joblib
```

## Level 2: direct SCM smoke test

```bash
python examples/run_one_scm_triplet.py --lmax 1 --n-quad 80
```

This is only a software smoke test.

## Level 3: article settings

```bash
rf3b scm-triplet \
  --coordinates data/triplet_example.json \
  --pair-map data/scm_pair_orientation_map_lmax6_beta2p5.npz \
  --lmax 6 \
  --n-quad 8000 \
  --n-orient 8 \
  --output outputs/triplet_scm.json
```

Publication numbers must be updated only from actual archived output generated with the declared settings.
