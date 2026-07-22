from pathlib import Path
from reprosec.capsule import initialize_directory, build_manifest
from reprosec.signing import generate_keypair, sign_manifest, verify_signature


def test_sign_and_verify(tmp_path: Path) -> None:
    root = tmp_path / "c"
    initialize_directory(root, "x")
    build_manifest(root)
    priv, pub = tmp_path / "k.pem", tmp_path / "k.pub.pem"
    generate_keypair(priv, pub)
    sign_manifest(root, priv)
    assert verify_signature(root, pub)
