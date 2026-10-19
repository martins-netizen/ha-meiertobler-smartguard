"""Regression checks for portable CI dependency updates."""

from __future__ import annotations

from pathlib import Path

import pytest
from packaging.markers import default_environment
from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def ci_requirements() -> list[Requirement]:
    """Read the same resolved requirements installed by the CI workflows."""
    return [
        Requirement(line)
        for line in (ROOT / ".github" / "requirements-ci.txt")
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
    environment = {
        key: str(value) for key, value in default_environment().items()
    }
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
