# External model asset

The trained `delta3_surrogate_corrected.joblib` file is not tracked in Git because its size is 5,767,044,032 bytes. It is archived under Zenodo DOI `10.5281/zenodo.21512150`.

Download and verify it with:

```bash
rf3b download-assets \
  --manifest data/asset_manifest.json \
  --destination data/external
```

The manifest declares the immutable filename, expected size, and SHA-256. A download is accepted only after both checks pass.

The refined pair map is small enough to remain version-controlled at:

```text
data/scm_pair_orientation_map_lmax6_beta2p5.npz
```

Its SHA-256 in this release is:

```text
a1e959250ee1af07af8ed16b90fb6f8c4c5c20b8a70c9c445d3134f0aa9d2a4d
```
