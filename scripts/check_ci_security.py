"""Require patched CI dependencies and offline uv during tests."""

import argparse
import os
import re
import sys
from importlib import metadata

MINIMUM_PYTHON = (3, 14, 10)
MINIMUM_PIP = (26, 2, 2)
MINIMUM_CERTIFI = (2026, 10, 19)
MINIMUM_UV = (0, 13, 4)
MINIMUM_MULTIDICT = (6, 9, 1)


class SecurityBaselineError(ValueError):
    """The environment does not meet the CI security policy."""


def stable_version(value: str) -> tuple[int, ...]:
    """Accept final numeric releases without bootstrap dependencies."""
    if re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,2}", value) is None:
        raise SecurityBaselineError("A final numeric package version is required.")
    parts = tuple(int(part) for part in value.split("."))
    return parts + (0,) * (3 - len(parts))


def package_version(name: str) -> str:
    """Read installed distribution metadata without exposing local paths."""
    try:
        value = metadata.version(name)
    except metadata.PackageNotFoundError as err:
        raise SecurityBaselineError(f"Required CI package is missing: {name}.") from err
    stable_version(value)
    return value


def require_minimum(name: str, minimum: tuple[int, ...]) -> str:
    """Reject an absent, prerelease, or outdated package."""
    value = package_version(name)
    if stable_version(value) < minimum:
        floor = ".".join(str(part) for part in minimum)
        raise SecurityBaselineError(f"CI requires {name}>={floor}.")
    return value


def check_security(stage: str, expected_ha: str | None = None) -> dict[str, str]:
    """Check before network installation and again before running tests."""
    if stage not in {"bootstrap", "installed"}:
        raise SecurityBaselineError("Unknown CI security check stage.")
    if (
        sys.version_info[:2] != MINIMUM_PYTHON[:2]
        or sys.version_info[:3] < MINIMUM_PYTHON
        or sys.version_info[3] != "final"
    ):
        raise SecurityBaselineError("CI requires Python 3.14.10 or newer in the 3.14 series.")
    report = {
        "Python": ".".join(str(part) for part in sys.version_info[:3]),
        "pip": require_minimum("pip", MINIMUM_PIP),
    }
    if stage == "bootstrap":
        return report

    # Check this even for newer uv, so dependency installs stay in the pip step.
    if os.environ.get("UV_OFFLINE") != "true":
        raise SecurityBaselineError("CI tests require UV_OFFLINE=true.")
    report["certifi"] = require_minimum("certifi", MINIMUM_CERTIFI)
    ha = package_version("homeassistant")
    if ha != expected_ha:
        raise SecurityBaselineError("Installed HA does not match the compatibility job.")
    report["HA"] = ha
    report["uv"] = require_minimum("uv", MINIMUM_UV)
    report["multidict"] = require_minimum("multidict", MINIMUM_MULTIDICT)
    report["UV_OFFLINE"] = "true"
    return report


def main() -> int:
    """Print version evidence or stop the job with a concise error."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("bootstrap", "installed"))
    parser.add_argument("--ha-version")
    args = parser.parse_args()
    if args.stage == "installed" and args.ha_version is None:
        parser.error("installed requires --ha-version")
    try:
        report = check_security(args.stage, args.ha_version)
    except SecurityBaselineError as err:
        print(f"CI security check failed: {err}", file=sys.stderr)
        return 1
    for name, value in report.items():
        print(f"{name}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
