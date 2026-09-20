"""Tests for the repository release gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.release import (
    INTEGRATION_RELATIVE,
    ROOT,
    ReleaseGateError,
    build_release,
    iter_release_files,
    read_version,
    verify_tag,
)


def _write_versions(root: Path, manifest_version: object, project_version: str) -> None:
    integration = root / INTEGRATION_RELATIVE
    integration.mkdir(parents=True)
    (integration / "manifest.json").write_text(
        json.dumps({"version": manifest_version}),
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        f'[project]\nversion = "{project_version}"\n',
        encoding="utf-8",
    )


def test_current_release_version_and_tag() -> None:
    """The repository version is stable and matches its prospective tag."""
    assert read_version() == "0.2.0"
    assert verify_tag("v0.2.0") == "0.2.0"


@pytest.mark.parametrize(
    "tag",
    ["0.2.0", "v0.2", "v0.2.0-beta.1", "v00.2.0", "release-v0.2.0"],
)
def test_release_tag_rejects_unsupported_forms(tag: str) -> None:
    """Only one exact stable semantic version form is accepted."""
    with pytest.raises(ReleaseGateError, match="stable form"):
        verify_tag(tag)


def test_release_tag_must_match_source_version() -> None:
    """A valid but different release tag cannot pass the gate."""
    with pytest.raises(ReleaseGateError, match="does not match"):
        verify_tag("v0.2.1")


def test_release_versions_must_match(tmp_path: Path) -> None:
    """Manifest and project metadata cannot drift apart."""
    _write_versions(tmp_path, "0.2.0", "0.2.1")

    with pytest.raises(ReleaseGateError, match="versions differ"):
        read_version(tmp_path)


def test_release_version_must_be_a_string(tmp_path: Path) -> None:
    """Malformed metadata is rejected before a package is built."""
    _write_versions(tmp_path, 2, "0.2.0")

    with pytest.raises(ReleaseGateError, match="must be strings"):
        read_version(tmp_path)


def test_build_release_is_deterministic(tmp_path: Path) -> None:
    """Two builds contain the same files and produce identical bytes."""
    first, first_checksum = build_release(tmp_path / "first")
    second, second_checksum = build_release(tmp_path / "second")

    assert first.read_bytes() == second.read_bytes()
    digest = hashlib.sha256(first.read_bytes()).hexdigest()
    assert first_checksum.read_text(encoding="utf-8") == f"{digest}  {first.name}\n"
    assert second_checksum.read_text(encoding="utf-8") == f"{digest}  {second.name}\n"

    release_names = [
        path.relative_to(ROOT).as_posix() for path in iter_release_files()
    ]
    with ZipFile(first) as bundle:
        assert bundle.namelist() == release_names
        assert all("__pycache__" not in name for name in bundle.namelist())
        assert all(not name.endswith(".pyc") for name in bundle.namelist())
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in bundle.infolist())


def test_release_source_rejects_symlinks(tmp_path: Path) -> None:
    """A symlink cannot smuggle an external file into the package."""
    _write_versions(tmp_path, "0.2.0", "0.2.0")
    outside = tmp_path / "outside.txt"
    outside.write_text("private", encoding="utf-8")
    (tmp_path / INTEGRATION_RELATIVE / "linked.txt").symlink_to(outside)

    with pytest.raises(ReleaseGateError, match="must not contain symlinks"):
        list(iter_release_files(tmp_path))
