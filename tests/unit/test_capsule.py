from pathlib import Path
import zipfile
from reprosec.capsule import initialize_directory, add_request, pack, verify_archive, safe_extract
from reprosec.models import RequestRecord


def test_pack_verify_and_determinism(tmp_path: Path) -> None:
    root = tmp_path / "c"
    initialize_directory(root, "demo")
    add_request(root, RequestRecord(method="GET", url="https://example.com"))
    a = pack(root, tmp_path / "a.rcap")
    b = pack(root, tmp_path / "b.rcap")
    assert a.read_bytes() == b.read_bytes()
    assert verify_archive(a) == []


def test_zip_slip_rejected(tmp_path: Path) -> None:
    z = tmp_path / "bad.rcap"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("../escape.txt", "x")
    try:
        safe_extract(z, tmp_path / "out")
    except ValueError as e:
        assert "unsafe" in str(e)
    else:
        raise AssertionError("zip slip accepted")
