# Updates

The official ReproSec update channel is zero-config:

```bash
reprosec update --check
reprosec update
reprosec update --force
```

Normal users do **not** provide a manifest or public key. SRIC resolves the fixed official `IsdarlinM/reprosec` channel, requires an immutable GitHub signature-verified release commit, validates the downloaded source ZIP and its `pyproject.toml`, backs up state, installs without a shell, and verifies the installed distribution version.

`reprosec update --check` verifies the official release metadata without installing. `reprosec update` installs a newer official release. `reprosec update --force` reinstalls the official release even when that exact version is already installed and uses pip `--force-reinstall` for that explicit force operation.

`--force` never permits a downgrade. `--check` and `--force` are mutually exclusive. Normal upgrades require rollback metadata matching the currently installed version; same-version force reinstalls use the verified target snapshot as the recovery package.

## Advanced custom channel

`--manifest` and `--public-key` remain available together for private/custom channels. The corresponding `REPROSEC_RELEASE_MANIFEST_URL` and `REPROSEC_RELEASE_PUBLIC_KEY` environment variables are also treated as an explicit custom-channel override. Supplying only one side is rejected.

Custom channels retain Ed25519 manifest verification and SHA-256 wheel verification. HTTP update sources and blind `git pull` remain prohibited.
