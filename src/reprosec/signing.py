from __future__ import annotations

import base64
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


def generate_keypair(private_path: Path, public_path: Path) -> None:
    key = Ed25519PrivateKey.generate()
    private_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )


def sign_manifest(root: Path, private_key_path: Path) -> Path:
    key = serialization.load_pem_private_key(private_key_path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("private key must be Ed25519")
    data = (root / "manifest.json").read_bytes()
    sig = key.sign(data)
    out = root / "signatures" / "manifest.ed25519"
    out.parent.mkdir(exist_ok=True)
    out.write_text(base64.b64encode(sig).decode("ascii") + "\n", encoding="ascii")
    return out


def verify_signature(root: Path, public_key_path: Path) -> bool:
    key = serialization.load_pem_public_key(public_key_path.read_bytes())
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("public key must be Ed25519")
    sig = base64.b64decode(
        (root / "signatures" / "manifest.ed25519").read_text(encoding="ascii").strip(),
        validate=True,
    )
    key.verify(sig, (root / "manifest.json").read_bytes())
    return True
