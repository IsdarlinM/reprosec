from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRIC_SHA = "9979d0dfb511d349361a55dc8dab7a204803d422"


def test_first_party_manifest_pins_exact_sric_commit() -> None:
    text = (ROOT / "requirements" / "first-party.txt").read_text(encoding="utf-8")
    assert f"sric-core @ https://github.com/IsdarlinM/sric-core/archive/{SRIC_SHA}.zip" in text


def test_installers_resolve_product_and_first_party_atomically() -> None:
    windows = (ROOT / "scripts" / "install-windows.cmd").read_text(encoding="utf-8")
    linux = (ROOT / "scripts" / "install-linux.sh").read_text(encoding="utf-8")
    assert '-r "$FIRST_PARTY" "$REPO_ROOT"' in linux
    assert '"$SRIC_CORE_SOURCE" "$REPO_ROOT"' in linux
    assert '-r "%FIRST_PARTY%" "%REPO_ROOT%"' in windows
    assert '"%SRIC_CORE_SOURCE%" "%REPO_ROOT%"' in windows
    assert '-c "$CONSTRAINTS" "$REPO_ROOT"' not in linux
    assert '-c "%CONSTRAINTS%" "%REPO_ROOT%"' not in windows
    for text in (windows, linux):
        assert "--force-reinstall" in text
        assert "pip check" in text
        assert "sric.web_console" in text
        assert "sric.web_workbench" in text
        assert "setuptools wheel" in text


def test_runtime_repair_path_python_and_help_contract() -> None:
    windows = (ROOT / "scripts" / "install-windows.cmd").read_text(encoding="utf-8")
    linux = (ROOT / "scripts" / "install-linux.sh").read_text(encoding="utf-8")
    assert '${PREFIX}/bin' in linux and 'BIN_DIR="${PREFIX}/bin"' in linux
    assert 'command -v python3' in linux and 'command -v python' in linux
    assert 'rm -rf "$VENV"' in linux and 'rm -rf "$INSTALL_ROOT"' not in linux
    assert "PATH_LINE='export PATH=\"$HOME/.local/bin:$PATH\"'" in linux
    assert 'set "PY_CMD=py -3"' in windows and 'set "PY_CMD=py -3.11"' not in windows
    assert '-m sric.install_path "%BIN_DIR%"' in windows
    assert "setx PATH" not in windows
    assert 'rmdir /s /q "%VENV%"' in windows and 'rmdir /s /q "%INSTALL_ROOT%"' not in windows
    assert '"$VENV/bin/$CMD" help' in linux
    assert '"%VENV%\\Scripts\\%CMD%.exe" help' in windows


def test_runtime_lock_matches_sric_patch() -> None:
    text = (ROOT / "requirements" / "runtime-py311.lock").read_text(encoding="utf-8")
    assert "sric-core==0.5.10" in text
