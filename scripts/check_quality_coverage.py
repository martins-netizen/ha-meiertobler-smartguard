"""Require complete statement and branch coverage for every integration module."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "custom_components/meiertobler_smartguard"


def validate(root: Path = ROOT) -> None:
    """Reject missing modules, disabled branch coverage and any uncovered code."""
    path = root / "coverage.json"
    if path.is_symlink() or not path.is_file():
        raise SystemExit("A regular coverage.json report is required")
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
        if report["meta"]["branch_coverage"] is not True:
            raise SystemExit("Branch coverage must be enabled")
        expected = {
            p.relative_to(root).as_posix() for p in (root / DOMAIN).rglob("*.py")
        }
        files = report["files"]
        if not expected or set(files) != expected:
            raise SystemExit("Coverage must include every integration Python module")
        for name, data in sorted(files.items()):
            summary = data["summary"]
            if (
                summary["num_statements"] != summary["covered_lines"]
                or summary["num_branches"] != summary["covered_branches"]
                or data["missing_lines"]
                or data["missing_branches"]
            ):
                raise SystemExit(f"Full statement and branch coverage required: {name}")
        totals = report["totals"]
        if (
            totals["num_statements"] != totals["covered_lines"]
            or totals["num_branches"] != totals["covered_branches"]
            or totals["percent_covered"] != 100
        ):
            raise SystemExit("Integration coverage must remain 100%")
    except (KeyError, TypeError, ValueError, OSError) as err:
        raise SystemExit("Coverage report is incomplete or invalid") from err
    print(f"All {len(expected)} integration modules: 100% statement and branch coverage")


if __name__ == "__main__":
    validate()
