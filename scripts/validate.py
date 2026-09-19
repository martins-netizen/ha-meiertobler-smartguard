#!/usr/bin/env python3
"""Validate repository structure without requiring Home Assistant imports."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "meiertobler_smartguard"
REQUIRED_FILES = (
    ROOT / ".github" / "CODEOWNERS",
    ROOT / ".github" / "dependabot.yml",
    ROOT / ".github" / "pull_request_template.md",
    ROOT / ".github" / "requirements-ci.in",
    ROOT / ".github" / "requirements-ci.txt",
    ROOT / ".github" / "workflows" / "validate.yml",
    ROOT / ".gitignore",
    ROOT / "CONTRIBUTING.md",
    ROOT / "README.md",
    ROOT / "LICENSE",
    ROOT / "SECURITY.md",
    ROOT / "hacs.json",
    INTEGRATION / "__init__.py",
    INTEGRATION / "api.py",
    INTEGRATION / "config_flow.py",
    INTEGRATION / "const.py",
    INTEGRATION / "coordinator.py",
    INTEGRATION / "entity.py",
    INTEGRATION / "select.py",
    INTEGRATION / "sensor.py",
    INTEGRATION / "manifest.json",
    INTEGRATION / "quality_scale.yaml",
    INTEGRATION / "strings.json",
    INTEGRATION / "translations" / "de.json",
    INTEGRATION / "translations" / "en.json",
)
SENSITIVE_PATTERNS = (
    re.compile(r"(?<![0-9])10\.(?:[0-9]{1,3}\.){2}[0-9]{1,3}(?![0-9])"),
    re.compile(r"(?<![0-9])192\.168\.(?:[0-9]{1,3}\.)[0-9]{1,3}(?![0-9])"),
    re.compile(
        r"(?<![0-9])172\.(?:1[6-9]|2[0-9]|3[01])\."
        r"(?:[0-9]{1,3}\.)[0-9]{1,3}(?![0-9])"
    ),
    re.compile(r"(?i)(?:[0-9a-f]{2}:){5}[0-9a-f]{2}"),
    re.compile(r"(?i)(password|passwd|api[_-]?key|token)\s*[:=]\s*['\"][^'\"]+['\"]"),
)
ACTION_REFERENCE = re.compile(r"uses:\s*[^\s@]+@([^\s#]+)")
FULL_GIT_SHA = re.compile(r"[0-9a-f]{40}")


def main() -> int:
    """Run deterministic local validation."""
    missing = [
        str(path.relative_to(ROOT)) for path in REQUIRED_FILES if not path.is_file()
    ]
    if missing:
        raise RuntimeError(f"Missing required files: {missing}")

    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    if manifest["domain"] != "meiertobler_smartguard":
        raise RuntimeError("Manifest domain mismatch")
    if manifest["version"] != "0.2.0":
        raise RuntimeError("Manifest version mismatch")
    if manifest.get("config_flow") is not True:
        raise RuntimeError("Config flow is not enabled")
    if manifest.get("requirements") != []:
        raise RuntimeError("Unexpected runtime dependency")

    workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(
        encoding="utf-8"
    )
    action_references = ACTION_REFERENCE.findall(workflow)
    if not action_references or any(
        FULL_GIT_SHA.fullmatch(reference) is None for reference in action_references
    ):
        raise RuntimeError("Every external GitHub Action must use a full commit SHA")

    for json_path in ROOT.rglob("*.json"):
        json.loads(json_path.read_text(encoding="utf-8"))
    for python_path in ROOT.rglob("*.py"):
        ast.parse(python_path.read_text(encoding="utf-8"), filename=str(python_path))

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix not in {
            ".in",
            ".json",
            ".md",
            ".py",
            ".toml",
            ".txt",
            ".yaml",
            ".yml",
        }:
            continue
        text = path.read_text(encoding="utf-8", errors="strict")
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(text):
                raise RuntimeError(
                    f"Sensitive-looking value in {path.relative_to(ROOT)}"
                )

    print("Repository validation: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
