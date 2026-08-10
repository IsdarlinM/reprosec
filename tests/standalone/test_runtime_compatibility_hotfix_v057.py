from __future__ import annotations

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


def test_stale_core_and_missing_current_web_runtime_are_detected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bootstrap.importlib.metadata, "version", lambda _name: "0.5.12")
    monkeypatch.setattr(
        bootstrap,
        "_find_module",
        lambda name: name in {"sric.web_console", "sric.web_workbench", "sric.web_catalog"},
    )
    result = bootstrap.status()
    assert result.compatible is False
    assert result.missing_modules == ("sric.web_runtime",)
    assert any("older than required 0.5.13" in reason for reason in result.reasons)


def test_complete_signed_transition_chain_reaches_current_floor(monkeypatch: pytest.MonkeyPatch) -> None:
    transitions: list[tuple[str, str]] = []
    monkeypatch.setattr(
        bootstrap,
        "_bridge_release",
        lambda *, current_version, target_version: transitions.append((current_version, target_version)),
    )
    assert bootstrap._bridge_to_current_floor("0.5.5") == "0.5.13"
    assert transitions == [
        ("0.5.5", "0.5.6"),
        ("0.5.6", "0.5.7"),
        ("0.5.7", "0.5.8"),
        ("0.5.8", "0.5.9"),
        ("0.5.9", "0.5.10"),
        ("0.5.10", "0.5.11"),
        ("0.5.11", "0.5.12"),
        ("0.5.12", "0.5.13"),
    ]


def test_bridge_release_uses_only_fixed_official_repository_and_commits(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
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
    bootstrap._bridge_release(current_version="0.5.12", target_version="0.5.13")
    downloads = [payload for kind, payload in calls if kind == "download"]
    assert {item["commit"] for item in downloads} == {
        bootstrap.SRIC_RELEASE_COMMITS["0.5.12"],
        bootstrap.SRIC_RELEASE_COMMITS["0.5.13"],
    }
    assert all(item["repository"] == "IsdarlinM/sric-core" for item in downloads)
    assert all(flag is True for kind, (_path, flag) in calls if kind == "install")


def test_same_version_missing_runtime_uses_fixed_signed_snapshot_repair(monkeypatch: pytest.MonkeyPatch) -> None:
    states = iter([
        _runtime("0.5.13", compatible=False, missing=("sric.web_runtime",)),
        _runtime("0.5.13", compatible=True),
    ])
    repairs: list[tuple[str, str]] = []
    monkeypatch.setattr(bootstrap, "status", lambda: next(states))
    monkeypatch.setattr(
        bootstrap,
        "_bridge_release",
        lambda *, current_version, target_version: repairs.append((current_version, target_version)),
    )
    monkeypatch.setattr(bootstrap.importlib, "invalidate_caches", lambda: None)
    assert bootstrap.ensure_for_official_update().compatible is True
    assert repairs == [("0.5.13", "0.5.13")]


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
    for args in (["--help"], ["-h"], ["help"]):
        assert runner.invoke(app, args).exit_code == 0
    for path, command in cli_by_path.items():
        args = path.split()
        assert runner.invoke(app, [*args, "--help"]).exit_code == 0, path
        assert runner.invoke(app, [*args, "-h"]).exit_code == 0, path
        normalized = normalize_help_argv(["reprosec", *args, "help"])
        assert normalized[-1] == "--help", path
        assert runner.invoke(app, normalized[1:]).exit_code == 0, path
        assert [p["name"] for p in command["params"]] == [p["name"] for p in web_by_path[path]["params"]]
