# Security policy

## Untrusted joblib and pickle files

The released surrogate is serialized with joblib and therefore uses Python pickle semantics. Loading a malicious or modified pickle can execute arbitrary code.

Only load the model downloaded from the associated Zenodo DOI and only after the SHA-256 has been verified against `data/asset_manifest.json`:

```text
75f58bd77a49b4dce61ffcfe2591f5183bdfc709e9dd25a1f2a2f9d7d42eed68
```

The command

```bash
rf3b download-assets --manifest data/asset_manifest.json --destination data/external
```

performs this verification automatically. Do not disable checksum verification and do not load model files received through email, chat, or unverified mirrors.

## Reporting a vulnerability

Use GitHub's private security-advisory mechanism for this repository. Do not disclose an exploitable issue in a public issue before maintainers have had an opportunity to assess it.
