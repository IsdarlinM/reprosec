# Signed updates

Configure `REPROSEC_RELEASE_MANIFEST_URL` and `REPROSEC_RELEASE_PUBLIC_KEY`, or pass them explicitly. `reprosec update --check` validates signature, product, version and release metadata without installing. Actual installation accepts only a signed, hash-matching wheel.
