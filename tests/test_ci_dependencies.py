"""Regression checks for portable CI dependency updates."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path

import pytest
import yaml
from homeassistant.util.yaml import load_yaml_dict
from packaging.markers import default_environment
from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def exported_requirements(tmp_path_factory: pytest.TempPathFactory) -> dict[str, str]:
    """CI must export the canonical lock offline without a warmed uv cache."""
    uv = shutil.which("uv")
    assert uv is not None, "The validation environment must supply uv"
    outputs = {}
    for group in ("ci", "ci-current", "build"):
        output = tmp_path_factory.mktemp("ci-exports") / f"{group}.txt"
        subprocess.run(
            [
                uv,
                "export",
                "--directory",
                str(ROOT / "ci"),
                "--locked",
                "--offline",
                "--python",
                sys.executable,
                "--no-python-downloads",
                "--only-group",
                group,
                "--no-emit-project",
                "--format",
                "requirements.txt",
                "--output-file",
                str(output),
            ],
            env={
                **os.environ,
                "UV_CACHE_DIR": str(tmp_path_factory.mktemp("uv-empty-cache")),
            },
            check=True,
            capture_output=True,
            text=True,
        )
        outputs[group] = output.read_text(encoding="utf-8")
    return outputs


@pytest.fixture(scope="module", params=["ci", "ci-current"])
def ci_group(request: pytest.FixtureRequest) -> str:
    return str(request.param)


@pytest.fixture(scope="module")
def ci_requirements(exported_requirements: dict[str, str], ci_group: str) -> list[Requirement]:
    """Read the resolved CI group rather than a second committed lockfile."""
    return [
        Requirement(line.removesuffix(" \\"))
        for line in exported_requirements[ci_group].splitlines()
        if line and not line.startswith(("#", " "))
    ]


@pytest.mark.parametrize(
    ("platform", "expected", "excluded"),
    [
        ("linux", {"dbus-fast"}, {"pyobjc-core", "winrt-runtime", "colorama"}),
        (
            "darwin",
            {"pyobjc-core", "pyobjc-framework-corebluetooth"},
            {"dbus-fast", "winrt-runtime", "colorama"},
        ),
        (
            "win32",
            {"winrt-runtime", "winrt-windows-foundation", "colorama"},
            {"dbus-fast", "pyobjc-core"},
        ),
    ],
)
def test_ci_requirements_preserve_platform_dependencies(
    ci_requirements: list[Requirement],
    platform: str,
    expected: set[str],
    excluded: set[str],
) -> None:
    """A Linux updater must retain the other platforms and their conditions."""
    environment = {key: str(value) for key, value in default_environment().items()}
    environment.update(
        {
            "sys_platform": platform,
            "platform_system": {
                "linux": "Linux",
                "darwin": "Darwin",
                "win32": "Windows",
            }[platform],
            "python_version": "3.14",
            "python_full_version": "3.14.10",
            "implementation_version": "3.14.10",
        }
    )
    selected = {
        requirement.name
        for requirement in ci_requirements
        if requirement.marker is None or requirement.marker.evaluate(environment)
    }
    assert expected <= selected
    assert not excluded & selected


@pytest.mark.parametrize("name", ["ci", "ci-current", "build"])
def test_requirements_pin_and_hash_every_package(
    name: str, exported_requirements: dict[str, str]
) -> None:
    """No dependency can bypass exact version and archive-integrity checks."""
    text = exported_requirements[name]
    requirements = [
        line
        for line in text.replace("\\\n", "").splitlines()
        if line and not line.startswith(("#", " "))
    ]
    assert requirements
    for line in requirements:
        raw_requirement, *hashes = line.split("--hash=sha256:")
        requirement = Requirement(raw_requirement.strip())
        specifiers = list(requirement.specifier)
        assert len(specifiers) == 1
        assert specifiers[0].operator == "=="
        assert "*" not in specifiers[0].version
        assert hashes
        for digest in hashes:
            assert len(digest.strip()) == 64
            assert all(character in "0123456789abcdef" for character in digest.strip())


@pytest.mark.parametrize("workflow", ["validate", "release"])
def test_ci_installation_enforces_hashes_and_source_allowlist(workflow: str) -> None:
    """All installs enforce hashes and permit a build only for pyric."""
    data = yaml.safe_load(
        (ROOT / ".github/workflows" / f"{workflow}.yml").read_text(encoding="utf-8")
    )
    steps = data["jobs"]["compatibility"]["steps"]
    installs = [step["run"] for step in steps if "pip install" in step.get("run", "")]
    assert len(installs) == 2
    for command in installs:
        assert "--require-hashes" in command
        assert "--only-binary=:all:" in command
    assert '-r "$RUNNER_TEMP/smartguard-build.txt"' in installs[0]
    assert "--no-binary" not in installs[0]
    assert '-r "$RUNNER_TEMP/smartguard-ci.txt"' in installs[1]
    assert "--no-binary=pyric" in installs[1].split()
    assert "--no-build-isolation" in installs[1]
    assert "--no-deps" in installs[1]
    assert any(step.get("run") == "python -m pip check" for step in steps)
    exports = [step["run"] for step in steps if "uv export" in step.get("run", "")]
    assert len(exports) == 1
    assert exports[0].count("--locked --offline") == 2
    assert "--only-group build" in exports[0]
    assert '--only-group "$CI_GROUP"' in exports[0]
    assert "--no-hashes" not in exports[0]
    setup = next(step for step in steps if "setup-uv@" in step.get("uses", ""))
    assert setup["with"]["version-file"] == "ci/uv.lock"


def test_home_assistant_lock_matches_minimum_and_fixture(
    ci_requirements: list[Requirement], ci_group: str,
) -> None:
    """Cover the advertised minimum and use matching fixtures for installed HA."""
    minimum = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))[
        "homeassistant"
    ]
    pins = {
        requirement.name: str(requirement.specifier)
        for requirement in ci_requirements
    }
    expected = minimum if ci_group == "ci" else "2026.11.1"
    assert pins["homeassistant"] == pins["pytest-homeassistant"] == f"=={expected}"
    blueprint_path = (
        ROOT
        / "blueprints"
        / "automation"
        / "martins_netizen"
        / "smartguard_guarded_night_heating.yaml"
    )
    blueprint = load_yaml_dict(blueprint_path)
    assert blueprint["blueprint"]["homeassistant"]["min_version"] == minimum
    assert version("homeassistant") == version("pytest-homeassistant")


def test_updater_keeps_the_coordinated_home_assistant_baseline() -> None:
    """Routine updates must honor HA's constraints without hiding alerts."""
    project = tomllib.loads((ROOT / "ci/pyproject.toml").read_text())
    minimum = json.loads((ROOT / "hacs.json").read_text())["homeassistant"]
    ci = [Requirement(raw) for raw in project["dependency-groups"]["ci"]]
    fixture = next(req for req in ci if req.name == "pytest-homeassistant")
    assert str(fixture.specifier) == f"=={minimum}"
    assert not {"pytest", "pytest-asyncio", "uv", "aiohttp", "yarl"} & {
        req.name for req in ci
    }
    updates = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text())["updates"]
    python = next(item for item in updates if item["package-ecosystem"] == "uv")
    assert python["directory"] == "/ci"
    assert python["versioning-strategy"] == "lockfile-only"
    assert not python.get("ignore")
    assert python["open-pull-requests-limit"] > 0
    assert not list((ROOT / ".github").glob("requirements-*.in"))
    assert not list((ROOT / ".github").glob("requirements-*.txt"))


def test_protected_quality_check_requires_compatibility() -> None:
    """A failed, absent or cancelled security/compatibility result blocks Quality."""
    data = yaml.safe_load((ROOT / ".github/workflows/validate.yml").read_text())
    jobs = data["jobs"]
    assert jobs["quality"]["name"] == "Quality"
    assert set(jobs["quality"]["needs"]) == {"compatibility", "advisories", "codeql"}
    assert jobs["quality"]["if"] == "${{ always() }}"
    gate = jobs["quality"]["steps"][0]
    keys = ["COMPATIBILITY_RESULT", "ADVISORIES_RESULT", "CODEQL_RESULT"]
    for key in keys:
        for result in ("success", "failure", "skipped", "cancelled", ""):
            env = dict.fromkeys(keys, "success")
            env[key] = result
            process = subprocess.run(["bash", "-c", gate["run"]], env=env, check=False)
            assert (process.returncode == 0) is (result == "success")
    assert any(
        "python -m pytest" in step.get("run", "")
        and "--cov-fail-under=100" in step["run"] and not step.get("if")
        for step in jobs["compatibility"]["steps"]
    )
    assert jobs["codeql"]["name"] == "Analyze Python"
    assert jobs["codeql"]["permissions"] == {"contents": "read", "security-events": "write"}
    for name, job in jobs.items():
        if name != "codeql":
            assert not job.get("permissions")
        for step in job["steps"]:
            if "uses" in step:
                assert len(step["uses"].split("@",1)[1]) == 40
            assert not step.get("continue-on-error")


def test_release_cannot_build_without_both_hAs_and_clean_advisories() -> None:
    data=yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text())
    jobs=data["jobs"]
    assert jobs["compatibility"]["strategy"]["matrix"]["include"] == [
        {"ha":"2026.11.0","group":"ci"}, {"ha":"2026.11.1","group":"ci-current"}]
    gate=jobs["release-gate"]
    assert set(gate["needs"]) == {"compatibility", "advisories"}
    assert gate["if"] == "${{ always() }}"
    command=gate["steps"][0]["run"]
    for key in ["COMPATIBILITY_RESULT", "ADVISORIES_RESULT"]:
        for result in ("success","failure","cancelled","skipped", ""):
            env=dict.fromkeys(["COMPATIBILITY_RESULT", "ADVISORIES_RESULT"],"success")
            env[key]=result
            p=subprocess.run(["bash","-c",command],env=env,check=False)
            assert (p.returncode==0) is (result=="success")
    steps=gate["steps"]
    guard=next(x for x in steps if "main ancestry" in x["name"])
    assert 'git merge-base --is-ancestor "$RELEASE_SHA" origin/main' in guard["run"]
    assert 'git cat-file -t' in guard["run"] and 'verify-tag' in guard["run"]
    assert steps.index(guard) < next(i for i,s in enumerate(steps) if "Build deterministic" in s["name"])
    assert data["permissions"]=={"contents":"read"}



def test_conflicting_fixture_groups_cannot_be_exported_together(tmp_path: Path) -> None:
    """The actual resolver must prevent a mixed minimum/current environment."""
    uv=shutil.which("uv")
    assert uv is not None
    process=subprocess.run([
        uv,"export","--directory",str(ROOT/"ci"),"--locked","--offline",
        "--no-default-groups","--group","ci","--group","ci-current","--no-emit-project",
        "--format","requirements.txt","--output-file",str(tmp_path/"invalid.txt"),
    ],capture_output=True,text=True,check=False)
    assert process.returncode != 0
    assert "conflict" in process.stderr.lower() or "incompatible" in process.stderr.lower()
    assert not (tmp_path/"invalid.txt").exists()
