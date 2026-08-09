from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from typer.testing import CliRunner

import reprosec.sric_bootstrap as bootstrap
from reprosec.api_all import _mount_degraded_workbench
from reprosec.cli_all import app, normalize_help_argv
from sric.web_console import build_command_catalog
from sric.web_workbench import build_feature_catalog, feature_contract


def _runtime(version: str, *, compatible: bool, missing: tuple[str, ...] = ()) -> bootstrap.SRICRuntimeStatus:
    return bootstrap.SRICRuntimeStatus(version, compatible, missing, (() if compatible else ("incompatible",)))


def test_reproduces_stale_core_detection_without_importing_new_sric_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bootstrap.importlib.metadata, "version", lambda _name: "0.5.5")
    monkeypatch.setattr(bootstrap, "_find_module", lambda _name: False)
    result = bootstrap.status()
    assert result.compatible is False
    assert result.missing_modules == ("sric.web_console", "sric.web_workbench")
    assert any("older than required 0.5.7" in reason for reason in result.reasons)


def test_signed_transition_bridges_use_only_exact_historical_commits(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    calls: list[tuple[str, object]] = []

    class FakeUpdater:
        def _download_official_archive(self, **kwargs):
            calls.append(("download", kwargs.copy()))
            return tmp_path / f"{kwargs['expected_version']}.zip"

        def install_verified_package(self, path, *, force_reinstall=False):
            calls.append(("install", (str(path), force_reinstall)))

        def _verify_installed_distribution(self, product, version):
            calls.append(("verify", (product, version)))

    monkeypatch.setattr(bootstrap, "_updater", lambda: FakeUpdater())
    monkeypatch.setattr(bootstrap.importlib, "invalidate_caches", lambda: None)
    bootstrap._upgrade_055_to_056()
    bootstrap._upgrade_056_to_057()

    downloads = [payload for kind, payload in calls if kind == "download"]
    assert {item["commit"] for item in downloads} == {
        bootstrap.SRIC_055_COMMIT,
        bootstrap.SRIC_056_COMMIT,
        bootstrap.SRIC_057_COMMIT,
    }
    assert all(item["repository"] == "IsdarlinM/sric-core" for item in downloads)
    assert all(flag is True for kind, (_path, flag) in calls if kind == "install")


def test_official_update_bridges_055_through_057_without_unsafe_channel_jump(monkeypatch: pytest.MonkeyPatch) -> None:
    states = iter([_runtime("0.5.5", compatible=False), _runtime("0.5.7", compatible=True)])
    bridges: list[str] = []
    updates: list[dict[str, object]] = []
    fake = SimpleNamespace(perform_product_update=lambda **kwargs: updates.append(kwargs))
    monkeypatch.setattr(bootstrap, "status", lambda: next(states))
    monkeypatch.setattr(bootstrap, "_upgrade_055_to_056", lambda: bridges.append("055-056"))
    monkeypatch.setattr(bootstrap, "_upgrade_056_to_057", lambda: bridges.append("056-057"))
    monkeypatch.setattr(bootstrap, "_updater", lambda: fake)
    monkeypatch.setattr(bootstrap, "_require_updater_api", lambda *_args: None)
    monkeypatch.setattr(bootstrap.importlib, "invalidate_caches", lambda: None)

    result = bootstrap.ensure_for_official_update()
    assert result.compatible is True
    assert bridges == ["055-056", "056-057"]
    assert updates == []


def test_corrupt_same_version_core_forces_reinstall(monkeypatch: pytest.MonkeyPatch) -> None:
    states = iter([
        _runtime("0.5.7", compatible=False, missing=("sric.web_workbench",)),
        _runtime("0.5.7", compatible=True),
    ])
    updates: list[dict[str, object]] = []
    fake = SimpleNamespace(perform_product_update=lambda **kwargs: updates.append(kwargs))
    monkeypatch.setattr(bootstrap, "status", lambda: next(states))
    monkeypatch.setattr(bootstrap, "_updater", lambda: fake)
    monkeypatch.setattr(bootstrap, "_require_updater_api", lambda *_args: None)
    monkeypatch.setattr(bootstrap.importlib, "invalidate_caches", lambda: None)
    bootstrap.ensure_for_official_update()
    assert updates == [{"expected_product": "sric-core", "current_version": "0.5.7", "check_only": False, "force": True}]


def test_degraded_workbench_is_503_not_process_import_failure() -> None:
    degraded = FastAPI()
    _mount_degraded_workbench(degraded, "missing sric.web_workbench")
    client = TestClient(degraded)
    page = client.get("/workbench")
    assert page.status_code == 503
    assert "runtime repair required" in page.text
    coverage = client.get("/api/v1/workbench/coverage")
    assert coverage.status_code == 503
    assert coverage.json()["complete"] is False


def test_every_public_cli_command_has_all_params_in_web_and_all_help_forms() -> None:
    cli = build_command_catalog("reprosec.cli_all")
    web = build_feature_catalog("reprosec.cli_all")
    assert feature_contract("reprosec.cli_all")["complete"] is True
    cli_by_path = {item["path"]: item for item in cli}
    web_by_path = {item["path"]: item for item in web}
    assert set(cli_by_path) == set(web_by_path)
    runner = CliRunner()
    assert runner.invoke(app, ["--help"]).exit_code == 0
    assert runner.invoke(app, ["-h"]).exit_code == 0
    assert runner.invoke(app, ["help"]).exit_code == 0
    for path, command in cli_by_path.items():
        args = path.split()
        assert runner.invoke(app, [*args, "--help"]).exit_code == 0, path
        assert runner.invoke(app, [*args, "-h"]).exit_code == 0, path
        normalized = normalize_help_argv(["reprosec", *args, "help"])
        assert normalized[-1] == "--help", path
        assert runner.invoke(app, normalized[1:]).exit_code == 0, path
        assert [p["name"] for p in command["params"]] == [p["name"] for p in web_by_path[path]["params"]]
