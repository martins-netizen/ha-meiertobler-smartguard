"""Tests for documentation and support-surface invariants."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "meiertobler_smartguard"


def test_documentation_is_linked_and_local_links_resolve() -> None:
    """Every maintained guide is discoverable and has valid local links."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required_guides = {
        "CHANGELOG.md",
        "docs/AUTOMATION_EXAMPLES.md",
        "docs/RELEASE_CHECKLIST.md",
        "docs/RELEASE_NOTES_0.3.0.md",
        "docs/TROUBLESHOOTING.md",
    }
    assert required_guides <= set(re.findall(r"\]\(([^)#]+\.md)(?:#[^)]+)?\)", readme))

    link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for markdown_path in ROOT.rglob("*.md"):
        for raw_target in link_pattern.findall(
            markdown_path.read_text(encoding="utf-8")
        ):
            target = raw_target.strip().split(maxsplit=1)[0]
            if target.startswith(("#", "mailto:", "http://", "https://")):
                continue
            resolved = (markdown_path.parent / target.split("#", 1)[0]).resolve()
            assert resolved.is_relative_to(ROOT)
            assert resolved.is_file(), f"Broken link: {markdown_path}: {target}"


def test_automation_examples_use_guarded_current_syntax() -> None:
    """Examples use placeholders, current syntax, and pre-write guards."""
    examples = (ROOT / "docs" / "AUTOMATION_EXAMPLES.md").read_text(encoding="utf-8")
    assert "triggers:" in examples
    assert "conditions:" in examples
    assert "actions:" in examples
    assert "action: select.select_option" in examples
    assert examples.count("select.replace_with_your_smartguard_mode_select") >= 5
    assert 'state: "auto"' in examples
    assert 'state: "heating"' in examples
    assert 'option: "heating"' in examples
    assert 'option: "auto"' in examples
    assert "docs-examples` quality rule" in examples


def test_automation_example_yaml_is_valid() -> None:
    """Every automation example is a valid standalone YAML mapping."""
    examples = (ROOT / "docs" / "AUTOMATION_EXAMPLES.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```yaml\n(.*?)\n```", examples, flags=re.DOTALL)
    assert len(blocks) == 3
    for block in blocks:
        automation = yaml.safe_load(block)
        assert isinstance(automation, dict)
        assert isinstance(automation.get("triggers"), list)
        assert isinstance(automation.get("conditions"), list)
        assert isinstance(automation.get("actions"), list)


def test_troubleshooting_and_quality_scale_are_consistent() -> None:
    """Troubleshooting has actionable structure without overstating examples."""
    troubleshooting = (ROOT / "docs" / "TROUBLESHOOTING.md").read_text(encoding="utf-8")
    assert troubleshooting.count("### Symptom") >= 5
    assert troubleshooting.count("### Description") >= 5
    assert troubleshooting.count("### Resolution") >= 5
    assert "The SmartGuard password is not requested" in troubleshooting
    assert "A selected operating mode is rejected or changes back" in troubleshooting

    quality_scale = (INTEGRATION / "quality_scale.yaml").read_text(encoding="utf-8")
    assert "docs-troubleshooting: done" in quality_scale
    assert re.search(
        r"docs-examples:\s*\n\s+status: todo\s*\n"
        r"\s+comment:.*blueprint",
        quality_scale,
    )


def test_issue_form_requires_privacy_confirmation() -> None:
    """The issue form blocks accidental disclosure by requiring confirmation."""
    issue_form = (ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").read_text(
        encoding="utf-8"
    )
    assert "internal IP addresses" in issue_form
    assert "serial numbers" in issue_form
    assert "unreviewed diagnostics" in issue_form
    assert "I removed private installation data" in issue_form
    assert issue_form.count("required: true") >= 7

    for path in sorted((ROOT / ".github" / "ISSUE_TEMPLATE").glob("*.yml")):
        assert isinstance(yaml.safe_load(path.read_text(encoding="utf-8")), dict)
