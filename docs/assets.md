# External assets

The trained `delta3_surrogate_corrected.joblib` file is not included in Git because its recorded size is 5,767,044,032 bytes.

After creating an immutable Zenodo model record:

1. Copy `data/asset_manifest.template.json` to `data/asset_manifest.json`.
2. Replace the placeholder download URLs.
3. Insert the verified SHA-256 for every asset.
4. Test the downloader:

```bash
rf3b download-assets \
  --manifest data/asset_manifest.json \
  --destination data/external
```

The canonical recorded model SHA-256 is already included in the template. The pair-map SHA-256 is generated in `reports/SOURCE_MANIFEST.json` for this starter package.
