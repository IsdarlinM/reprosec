from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRIC_SHA = "6217b4e0b8b1a7b69f2f64181d1e3b22fd4bc221"


def test_first_party_manifest_pins_exact_sric_commit() -> None:
    text = (ROOT / "requirements" / "first-party.txt").read_text(encoding="utf-8")
    assert f"sric-core @ https://github.com/IsdarlinM/sric-core/archive/{SRIC_SHA}.zip" in text


def test_installers_bootstrap_first_party_dependencies() -> None:
    windows = (ROOT / "scripts" / "install-windows.cmd").read_text(encoding="utf-8")
    linux = (ROOT / "scripts" / "install-linux.sh").read_text(encoding="utf-8")
    assert '-r "%FIRST_PARTY%"' in windows
    assert '-r "$FIRST_PARTY"' in linux


def test_runtime_lock_matches_sric_patch() -> None:
    text = (ROOT / "requirements" / "runtime-py311.lock").read_text(encoding="utf-8")
    assert "sric-core==0.5.5" in text
