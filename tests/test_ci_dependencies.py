"""Regression checks for portable CI dependency updates."""

from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import pytest
import yaml
from packaging.markers import default_environment
from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module", params=["ci", "ci-minimum"])
def ci_requirements(request: pytest.FixtureRequest) -> list[Requirement]:
    """Read the same resolved requirements installed by the CI workflows."""
    return [
        Requirement(line.removesuffix(" \\"))
        for line in (ROOT / ".github" / f"requirements-{request.param}.txt")
        .read_text(encoding="utf-8")
        .splitlines()
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
            "python_full_version": "3.14.2",
            "implementation_version": "3.14.2",
        }
    )
    selected = {
        requirement.name
        for requirement in ci_requirements
        if requirement.marker is None or requirement.marker.evaluate(environment)
    }
    assert expected <= selected
    assert not excluded & selected


@pytest.mark.parametrize("name", ["ci", "ci-minimum", "build"])
def test_requirements_pin_and_hash_every_package(name: str) -> None:
    """No dependency can bypass exact version and archive-integrity checks."""
    text = (ROOT / ".github" / f"requirements-{name}.txt").read_text(encoding="utf-8")
    assert "--generate-hashes" in text.splitlines()[1]
    assert "--universal" in text.splitlines()[1]
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
    """All installs enforce hashes; only two reviewed packages may build."""
    data = yaml.safe_load(
        (ROOT / ".github/workflows" / f"{workflow}.yml").read_text(encoding="utf-8")
    )
    steps = [step for job in data["jobs"].values() for step in job["steps"]]
    installs = [step["run"] for step in steps if "pip install" in step.get("run", "")]
    assert len(installs) == 2
    for command in installs:
        assert "--require-hashes" in command
        assert "--only-binary=:all:" in command
    assert "-r .github/requirements-build.txt" in installs[0]
    assert "--no-binary" not in installs[0]
    requirements = (
        "${{ matrix.requirements }}" if workflow == "validate" else "ci"
    )
    assert f"-r .github/requirements-{requirements}.txt" in installs[1]
    assert "--no-binary=mock-open,pyric" in installs[1]
    assert "--no-build-isolation" in installs[1]
    assert "--no-deps" in installs[1]
    assert any(step.get("run") == "python -m pip check" for step in steps)


def test_installed_home_assistant_matches_fixture_package() -> None:
    """Do not report a baseline test using a different installed HA release."""
    minimum = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))[
        "homeassistant"
    ]
    try:
        expected = version("pytest-homeassistant")
    except PackageNotFoundError:
        assert version("pytest-homeassistant-custom-component") == "0.13.363"
        expected = minimum
    assert version("homeassistant") == expected


def test_protected_quality_check_requires_all_compatibility_jobs() -> None:
    """A failed or cancelled matrix must never leave the protected check green."""
    data = yaml.safe_load(
        (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    )
    jobs = data["jobs"]
    assert jobs["quality"]["name"] == "Quality"
    assert jobs["quality"]["needs"] == "compatibility"
    assert jobs["quality"]["if"] == "${{ always() }}"
    gate = jobs["quality"]["steps"][0]
    assert gate["env"]["COMPATIBILITY_RESULT"] == "${{ needs.compatibility.result }}"
    assert gate["run"] == 'test "$COMPATIBILITY_RESULT" = success'
    test_job = jobs["compatibility"]
    assert test_job["strategy"]["fail-fast"] is False
    assert {
        entry["requirements"] for entry in test_job["strategy"]["matrix"]["include"]
    } == {"ci", "ci-minimum"}
    assert any(
        "python -m pytest" in step.get("run", "")
        and "--cov-fail-under=95" in step["run"]
        and not step.get("if")
        for step in test_job["steps"]
    )
