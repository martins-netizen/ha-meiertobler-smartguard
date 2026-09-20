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
BLUEPRINT = (
    ROOT
    / "blueprints"
    / "automation"
    / "martins_netizen"
    / "smartguard_guarded_night_heating.yaml"
)
REQUIRED_FILES = (
    ROOT / ".github" / "CODEOWNERS",
    ROOT / ".github" / "dependabot.yml",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml",
    ROOT / ".github" / "pull_request_template.md",
    ROOT / ".github" / "requirements-ci.in",
    ROOT / ".github" / "requirements-ci.txt",
    ROOT / ".github" / "workflows" / "validate.yml",
    ROOT / ".github" / "workflows" / "release.yml",
    ROOT / ".gitignore",
    BLUEPRINT,
    ROOT / "CONTRIBUTING.md",
    ROOT / "docs" / "AUTOMATION_EXAMPLES.md",
    ROOT / "docs" / "RELEASE_CHECKLIST.md",
    ROOT / "docs" / "TROUBLESHOOTING.md",
    ROOT / "README.md",
    ROOT / "LICENSE",
    ROOT / "SECURITY.md",
    ROOT / "scripts" / "__init__.py",
    ROOT / "scripts" / "release.py",
    ROOT / "hacs.json",
    INTEGRATION / "__init__.py",
    INTEGRATION / "api.py",
    INTEGRATION / "config_flow.py",
    INTEGRATION / "const.py",
    INTEGRATION / "coordinator.py",
    INTEGRATION / "diagnostics.py",
    INTEGRATION / "entity.py",
    INTEGRATION / "select.py",
    INTEGRATION / "sensor.py",
    INTEGRATION / "brand" / "icon.png",
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
    re.compile(r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----"),
    re.compile(r"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{20,}"),
)
ACTION_REFERENCE = re.compile(r"uses:\s*[^\s@]+@([^\s#]+)")
FULL_GIT_SHA = re.compile(r"[0-9a-f]{40}")
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def _validate_local_markdown_links() -> None:
    """Require every relative Markdown link to resolve inside the repository."""
    for markdown_path in ROOT.rglob("*.md"):
        content = markdown_path.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK.findall(content):
            target = raw_target.strip().split(maxsplit=1)[0]
            if target.startswith(("#", "mailto:", "http://", "https://")):
                continue
            relative_target = target.split("#", 1)[0]
            resolved = (markdown_path.parent / relative_target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError as err:
                raise RuntimeError(
                    f"Markdown link escapes repository: {markdown_path.relative_to(ROOT)}"
                ) from err
            if not resolved.is_file():
                raise RuntimeError(
                    "Broken local Markdown link in "
                    f"{markdown_path.relative_to(ROOT)}: {target}"
                )


def _validate_documentation() -> None:
    """Validate user documentation and privacy-sensitive support surfaces."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for target in (
        "docs/AUTOMATION_EXAMPLES.md",
        "docs/RELEASE_CHECKLIST.md",
        "docs/TROUBLESHOOTING.md",
    ):
        if target not in readme:
            raise RuntimeError(f"README does not link to {target}")

    troubleshooting = (ROOT / "docs" / "TROUBLESHOOTING.md").read_text(encoding="utf-8")
    for heading in ("### Symptom", "### Description", "### Resolution"):
        if troubleshooting.count(heading) < 5:
            raise RuntimeError(f"Troubleshooting structure is incomplete: {heading}")

    examples = (ROOT / "docs" / "AUTOMATION_EXAMPLES.md").read_text(encoding="utf-8")
    required_example_fragments = (
        "triggers:",
        "conditions:",
        "actions:",
        "action: select.select_option",
        "select.replace_with_your_smartguard_mode_select",
        'option: "heating"',
        'option: "auto"',
    )
    if any(fragment not in examples for fragment in required_example_fragments):
        raise RuntimeError("Automation examples are missing a required safety pattern")
    if "smartguard_guarded_night_heating.yaml" not in examples:
        raise RuntimeError("Automation documentation does not link to the blueprint")

    blueprint = BLUEPRINT.read_text(encoding="utf-8")
    required_blueprint_fragments = (
        "domain: automation",
        "min_version: 2026.9.0",
        "integration: meiertobler_smartguard",
        "id: select_heating",
        "id: return_auto",
        "is_state(enable_helper_entity, 'on')",
        "is_state(mode_select_entity, 'auto')",
        "is_state(operating_status_entity, 'cooling')",
        "<= (maximum_temperature | float)",
        "is_state(mode_select_entity, 'heating')",
        "action: select.select_option",
        "option: heating",
        "option: auto",
    )
    if any(fragment not in blueprint for fragment in required_blueprint_fragments):
        raise RuntimeError("SmartGuard blueprint is missing a required safeguard")
    if "source_url:" in blueprint:
        raise RuntimeError("Private blueprint must not claim a public source URL")

    quality_scale = (INTEGRATION / "quality_scale.yaml").read_text(encoding="utf-8")
    if "docs-troubleshooting: done" not in quality_scale:
        raise RuntimeError("Troubleshooting quality rule must be marked done")
    if not re.search(
        r"docs-examples:\s*\n\s+status: todo\s*\n"
        r"\s+comment:.*blueprint",
        quality_scale,
    ):
        raise RuntimeError(
            "Documentation examples must remain todo until a blueprint is published"
        )

    issue_form = (ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").read_text(
        encoding="utf-8"
    )
    for privacy_term in (
        "credentials",
        "internal IP addresses",
        "serial numbers",
        "unreviewed diagnostics",
    ):
        if privacy_term not in issue_form:
            raise RuntimeError(f"Issue form privacy warning missing: {privacy_term}")

    _validate_local_markdown_links()


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

    hacs_manifest = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    if not isinstance(hacs_manifest, dict):
        raise RuntimeError("hacs.json must contain a JSON object")
    if hacs_manifest.get("name") != "Meier Tobler SmartGuard":
        raise RuntimeError("HACS display name mismatch")
    if hacs_manifest.get("content_in_root") is not False:
        raise RuntimeError(
            "HACS integration content must remain under custom_components"
        )
    if hacs_manifest.get("country") != "CH":
        raise RuntimeError("HACS country must be CH")
    unsupported_hacs_keys = set(hacs_manifest) - {
        "content_in_root",
        "country",
        "filename",
        "hacs",
        "hide_default_branch",
        "homeassistant",
        "name",
        "persistent_directory",
        "zip_release",
    }
    if unsupported_hacs_keys:
        raise RuntimeError(
            f"Unsupported hacs.json keys: {sorted(unsupported_hacs_keys)}"
        )

    icon = (INTEGRATION / "brand" / "icon.png").read_bytes()
    if not icon.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("Brand icon is not a PNG file")

    _validate_documentation()

    for workflow_path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        workflow = workflow_path.read_text(encoding="utf-8")
        if "pull_request_target:" in workflow:
            raise RuntimeError(
                f"Privileged pull_request_target trigger in {workflow_path.name}"
            )
        if "permissions:\n  contents: read" not in workflow:
            raise RuntimeError(
                f"Workflow must declare read-only contents access: {workflow_path.name}"
            )
        if re.search(r"(?m)^\s+contents:\s+write\s*$", workflow):
            raise RuntimeError(
                f"Workflow must not grant contents write access: {workflow_path.name}"
            )
        action_references = ACTION_REFERENCE.findall(workflow)
        if not action_references or any(
            FULL_GIT_SHA.fullmatch(reference) is None for reference in action_references
        ):
            raise RuntimeError(
                "Every external GitHub Action must use a full commit SHA: "
                f"{workflow_path.name}"
            )

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
