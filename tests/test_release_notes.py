"""Publication evidence must match the version actually being validated."""

from __future__ import annotations

import pytest

from scripts.validate import ROOT, validate_release_notes

CANDIDATE_NOTES = (
    "# Release notes: 0.4.0\n\n"
    "Status: release candidate\n\n"
    "This candidate is not yet published. The annotated `v0.4.0` tag is pending.\n"
)


def test_candidate_fixture_passes() -> None:
    """Candidate validation stays covered after the repository publishes a release."""
    validate_release_notes("0.4.0", CANDIDATE_NOTES)


def test_prepared_and_historical_release_notes_pass() -> None:
    """A prepared version must not borrow the previous release's publication."""
    for version in ("0.3.0", "0.4.0"):
        notes = (ROOT / "docs" / f"RELEASE_NOTES_{version}.md").read_text(encoding="utf-8")
        validate_release_notes(version, notes)


@pytest.mark.parametrize(
    "change",
    ["unsupported_status", "ambiguous_status", "publication_claim", "wrong_version", "wrong_tag"],
)
def test_candidate_rejects_misleading_or_mismatched_metadata(change: str) -> None:
    """Preparation cannot pass with missing or contradictory release identity."""
    notes = CANDIDATE_NOTES
    if change == "unsupported_status":
        notes = notes.replace("Status: release candidate", "Status: ready")
    elif change == "ambiguous_status":
        notes += "\nStatus: published release\n"
    elif change == "publication_claim":
        notes = notes.replace("not yet published", "already published")
    elif change == "wrong_version":
        notes = notes.replace("# Release notes: 0.4.0", "# Release notes: 0.3.0")
    else:
        notes = notes.replace("annotated `v0.4.0` tag", "annotated `v0.3.0` tag")
    assert notes != CANDIDATE_NOTES
    with pytest.raises(RuntimeError):
        validate_release_notes("0.4.0", notes)


def test_published_version_needs_its_own_link_and_checksum() -> None:
    """An old release URL or missing checksum cannot prove a new publication."""
    notes = (ROOT / "docs/RELEASE_NOTES_0.3.0.md").read_text(encoding="utf-8")
    relabelled = notes.replace("# Release notes: 0.3.0", "# Release notes: 0.4.0").replace(
        "annotated `v0.3.0` tag", "annotated `v0.4.0` tag"
    )
    with pytest.raises(RuntimeError, match="own version"):
        validate_release_notes("0.4.0", relabelled)
    without_digest = notes.replace(
        "190b3aeb71e43fed8592242416ed5cd702bdbc9c2e82bdb279b4cea4d9209dc5", "pending"
    )
    with pytest.raises(RuntimeError, match="SHA-256"):
        validate_release_notes("0.3.0", without_digest)
