from pathlib import Path


def test_linux_uninstall_preserves_user_data_tree() -> None:
    root = Path(__file__).resolve().parents[2]
    script = (root / "scripts" / "uninstall-linux.sh").read_text(encoding="utf-8")
    assert 'rm -rf "$INSTALL_ROOT"' not in script
    assert 'rm -rf "$INSTALL_ROOT/venv"' in script
