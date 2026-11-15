"""Keep the coverage gate strict even if a rounded total still looks complete."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.check_quality_coverage import DOMAIN, validate


@pytest.fixture
def complete_report(tmp_path: Path) -> tuple[Path, dict]:
    module = tmp_path / DOMAIN / "sample.py"
    module.parent.mkdir(parents=True)
    module.write_text("value = 1\n")
    summary = {
        "num_statements": 2, "covered_lines": 2,
        "num_branches": 2, "covered_branches": 2, "percent_covered": 100,
    }
    data = {
        "meta": {"branch_coverage": True},
        "files": {f"{DOMAIN}/sample.py": {
            "summary": summary, "missing_lines": [], "missing_branches": [],
        }},
        "totals": copy.deepcopy(summary),
    }
    return tmp_path, data


def test_complete_report_is_accepted(complete_report: tuple[Path, dict]) -> None:
    root, data = complete_report
    (root / "coverage.json").write_text(json.dumps(data))
    validate(root)


@pytest.mark.parametrize("failure", [
    "line", "branch", "counter", "missing_module", "new_module", "extra_file",
    "branches_disabled", "rounded_total", "invalid_schema",
])
def test_missing_or_uncovered_code_fails_closed(
    complete_report: tuple[Path, dict], failure: str,
) -> None:
    root, data = complete_report
    file = data["files"][f"{DOMAIN}/sample.py"]
    if failure == "line":
        file["missing_lines"] = [1]
    elif failure == "branch":
        file["missing_branches"] = [[1, 2]]
    elif failure == "counter":
        file["summary"]["covered_branches"] = 1
    elif failure == "missing_module":
        data["files"] = {}
    elif failure == "new_module":
        (root / DOMAIN / "new.py").write_text("value = 2\n")
    elif failure == "extra_file":
        data["files"]["unrelated.py"] = copy.deepcopy(file)
    elif failure == "branches_disabled":
        data["meta"]["branch_coverage"] = False
    elif failure == "rounded_total":
        data["totals"]["percent_covered"] = 99.999
    elif failure == "invalid_schema":
        data = {}
    (root / "coverage.json").write_text(json.dumps(data))
    with pytest.raises(SystemExit):
        validate(root)


def test_symlink_missing_and_invalid_reports_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        validate(tmp_path)
    report = tmp_path / "coverage.json"
    report.symlink_to(tmp_path / "elsewhere.json")
    with pytest.raises(SystemExit):
        validate(tmp_path)
    report.unlink()
    report.write_text("{")
    with pytest.raises(SystemExit, match="incomplete or invalid"):
        validate(tmp_path)
