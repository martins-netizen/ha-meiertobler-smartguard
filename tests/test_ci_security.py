"""Regression tests for the CI security and HA compatibility baseline."""

import json
import os
import subprocess
import sys
import tomllib
from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib import metadata, util
from pathlib import Path
from threading import Thread

import pytest
import yaml

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_ci_security.py"
SPEC = util.spec_from_file_location("check_ci_security", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
security = util.module_from_spec(SPEC)
SPEC.loader.exec_module(security)


@pytest.fixture
def secure_environment(monkeypatch):
    """Represent the minimum HA fixture with patched installer and CA bundle."""
    versions = {
        "pip": "26.2.2",
        "certifi": "2026.10.19",
        "homeassistant": "2026.11.0",
        "uv": "0.13.6",
        "multidict": "6.9.1",
    }

    def installed_version(name):
        if name not in versions:
            raise metadata.PackageNotFoundError(name)
        return versions[name]

    monkeypatch.setattr(security.metadata, "version", installed_version)
    monkeypatch.setattr(security.sys, "version_info", (3, 14, 10, "final", 0))
    monkeypatch.setenv("UV_OFFLINE", "true")
    return versions


@pytest.mark.parametrize("pip", ["26.2.1", "26.1", "26.2.2rc1"])
def test_bootstrap_rejects_stale_or_prerelease_pip(secure_environment, pip):
    secure_environment["pip"] = pip
    with pytest.raises(security.SecurityBaselineError):
        security.check_security("bootstrap")


@pytest.mark.parametrize("name", ["certifi", "homeassistant", "uv", "multidict"])
def test_bootstrap_does_not_require_uninstalled_test_dependencies(secure_environment, name):
    del secure_environment[name]
    assert security.check_security("bootstrap")["pip"] == "26.2.2"


@pytest.mark.parametrize(
    "python",
    [(3, 14, 9, "final", 0), (3, 15, 2, "final", 0), (3, 14, 11, "candidate", 1)],
)
def test_rejects_stale_wrong_minor_or_prerelease_python(secure_environment, monkeypatch, python):
    monkeypatch.setattr(security.sys, "version_info", python)
    with pytest.raises(security.SecurityBaselineError, match="Python"):
        security.check_security("bootstrap")


@pytest.mark.parametrize("certifi", ["2026.10.18", "2026.7.22", "2026.10.19.dev1"])
def test_installed_rejects_stale_or_prerelease_ca_bundle(secure_environment, certifi):
    secure_environment["certifi"] = certifi
    with pytest.raises(security.SecurityBaselineError):
        security.check_security("installed", "2026.11.0")


@pytest.mark.parametrize("value", [None, "", "false", "0"])
@pytest.mark.parametrize("uv", ["0.12.23", "0.13.4"])
def test_uv_requires_offline_mode_even_when_patched(secure_environment, monkeypatch, value, uv):
    secure_environment["uv"] = uv
    if value is None:
        monkeypatch.delenv("UV_OFFLINE")
    else:
        monkeypatch.setenv("UV_OFFLINE", value)
    with pytest.raises(security.SecurityBaselineError, match="UV_OFFLINE"):
        security.check_security("installed", "2026.11.0")


@pytest.mark.parametrize(
    "ha,uv",
    [
        ("2026.8.3", "0.11.31"),
        ("2026.11.0", "0.11.31"),
        ("2026.11.0", "0.12.23"),
        ("2026.11.1", "0.13.3"),
    ],
)
def test_offline_uv_must_meet_security_floor(secure_environment, ha, uv):
    secure_environment.update(homeassistant=ha, uv=uv)
    with pytest.raises(security.SecurityBaselineError, match=r"uv>=0\.13\.4"):
        security.check_security("installed", ha)


def test_installed_ha_must_match_the_matrix(secure_environment):
    with pytest.raises(security.SecurityBaselineError, match="does not match"):
        security.check_security("installed", "2026.11.1")


@pytest.mark.parametrize("name", ["pip", "certifi", "homeassistant", "uv", "multidict"])
def test_missing_required_distribution_fails_closed(secure_environment, name):
    del secure_environment[name]
    with pytest.raises(security.SecurityBaselineError, match="missing"):
        security.check_security("installed", "2026.11.0")


def test_installed_ha_uses_patched_uv(secure_environment):
    report = security.check_security("installed", "2026.11.0")
    assert report["uv"] == "0.13.6"
    assert report["UV_OFFLINE"] == "true"


def test_advertised_minimum_matches_ci_and_fixture_pins():
    root = SCRIPT.parents[1]
    minimum = json.loads((root / "hacs.json").read_text())["homeassistant"]
    workflow = yaml.safe_load((root / ".github/workflows/validate.yml").read_text())
    matrix = workflow["jobs"]["compatibility"]["strategy"]["matrix"]["include"]
    fixtures = {case["group"]: case["ha"] for case in matrix}
    assert fixtures == {"ci": minimum, "ci-current": "2026.11.1"}
    project = tomllib.loads((root / "ci/pyproject.toml").read_text())
    for group, ha in fixtures.items():
        assert f"pytest-homeassistant=={ha}" in project["dependency-groups"][group]
    assert project["tool"]["uv"]["conflicts"] == [[{"group": "ci"}, {"group": "ci-current"}]]


@pytest.mark.parametrize("value", ["6.9.0", "6.9.1rc1"])
def test_installed_multidict_must_meet_security_floor(secure_environment, value):
    secure_environment["multidict"] = value
    with pytest.raises(security.SecurityBaselineError):
        security.check_security("installed", "2026.11.0")


def test_newer_final_releases_are_accepted(secure_environment, monkeypatch):
    secure_environment.update(pip="27.0", certifi="2026.10.23", uv="0.13.5")
    monkeypatch.setattr(security.sys, "version_info", (3, 14, 11, "final", 0))
    assert security.check_security("installed", "2026.11.0")["uv"] == "0.13.5"


def test_cli_failure_is_nonzero_and_does_not_expose_paths(secure_environment, monkeypatch, capsys):
    secure_environment["pip"] = "26.2.1"
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "bootstrap"])
    assert security.main() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == "CI security check failed: CI requires pip>=26.2.2."


def test_installed_uv_honours_offline_environment(socket_enabled, tmp_path):
    """Probe the real pinned binary; the control can reach only a local index."""
    requests = []

    class IndexHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            self.send_response(404)
            self.end_headers()

        def log_message(self, *_args):
            """Do not put request URLs in the test log."""

    server = HTTPServer(("127.0.0.1", 0), IndexHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    command = [
        sys.executable, "-m", "uv", "--no-config", "--no-cache", "pip", "compile",
        "--python", sys.executable,
        "--index-url", f"http://127.0.0.1:{server.server_port}/simple/", "-",
    ]
    # Do not inherit extra package indexes, proxies, credentials, or uv overrides.
    env = {
        "PATH": os.environ["PATH"],
        "UV_OFFLINE": "true",
        "UV_PYTHON_DOWNLOADS": "never",
    }
    try:
        offline = subprocess.run(
            command, input="smartguard-ci-offline-probe-nonexistent==0.0.0\n",
            env=env, cwd=tmp_path, text=True, capture_output=True, timeout=15, check=False,
        )
        assert offline.returncode != 0
        assert requests == []

        control = subprocess.run(
            command, input="smartguard-ci-offline-probe-nonexistent==0.0.0\n",
            env={**env, "UV_OFFLINE": "false"}, cwd=tmp_path,
            text=True, capture_output=True, timeout=15, check=False,
        )
        assert control.returncode != 0
        assert requests  # Proves the same binary/command can reach the local detector.
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


@pytest.mark.parametrize("permission", ["contents", "actions", "id-token", "packages"])
def test_no_workflow_can_gain_unrelated_write_permissions(permission):
    from scripts.validate import validate_workflow_permissions
    source = "permissions:\n  contents: read\n\njobs:\n  unsafe:\n    permissions:\n      " + permission + ": write\n"
    with pytest.raises(RuntimeError, match="write permission"):
        validate_workflow_permissions("validate.yml", source)


def test_codeql_security_upload_permission_has_no_global_or_release_exception():
    from scripts.validate import validate_workflow_permissions
    source = ("permissions:\n  contents: read\njobs:\n  codeql:\n"
              "    permissions:\n      contents: read\n      security-events: write\n")
    validate_workflow_permissions("validate.yml", source)
    with pytest.raises(RuntimeError):
        validate_workflow_permissions("release.yml", source)
    with pytest.raises(RuntimeError):
        validate_workflow_permissions("validate.yml", "permissions:\n  contents: read\n  security-events: write\n")
