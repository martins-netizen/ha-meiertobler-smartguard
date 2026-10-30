"""Tests for the repository release gate."""

from __future__ import annotations

import hashlib
import json
import shutil
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


def _write_versions(
    root: Path,
    manifest_version: object,
    project_version: str,
    lock_version: str | None = None,
) -> None:
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
    (root / "uv.lock").write_text(
        "version = 1\n\n[[package]]\n"
        'name = "ha-meiertobler-smartguard"\n'
        f'version = "{lock_version or project_version}"\n',
        encoding="utf-8",
    )


def test_current_release_version_and_tag() -> None:
    """The repository version is stable and matches its prospective tag."""
    assert read_version() == "0.5.0"
    assert verify_tag("v0.5.0") == "0.5.0"


@pytest.mark.parametrize(
    "tag",
    ["0.3.0", "v0.3", "v0.3.0-beta.1", "v00.3.0", "release-v0.3.0"],
)
def test_release_tag_rejects_unsupported_forms(tag: str) -> None:
    """Only one exact stable semantic version form is accepted."""
    with pytest.raises(ReleaseGateError, match="stable form"):
        verify_tag(tag)


def test_release_tag_must_match_source_version() -> None:
    """A valid but different release tag cannot pass the gate."""
    with pytest.raises(ReleaseGateError, match="does not match"):
        verify_tag("v0.3.1")


def test_release_versions_must_match(tmp_path: Path) -> None:
    """Manifest and project metadata cannot drift apart."""
    _write_versions(tmp_path, "0.3.0", "0.3.1")

    with pytest.raises(ReleaseGateError, match="versions differ"):
        read_version(tmp_path)


def test_release_version_must_be_a_string(tmp_path: Path) -> None:
    """Malformed metadata is rejected before a package is built."""
    _write_versions(tmp_path, 3, "0.3.0")

    with pytest.raises(ReleaseGateError, match="must be unique strings"):
        read_version(tmp_path)


def test_release_lock_version_must_match(tmp_path: Path) -> None:
    """The lock-file root package cannot drift from release metadata."""
    _write_versions(tmp_path, "0.3.0", "0.3.0", "0.3.1")

    with pytest.raises(ReleaseGateError, match="versions differ"):
        read_version(tmp_path)


def test_release_documents_describe_published_release() -> None:
    """The release notes identify the immutable published version."""
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    release_notes = (ROOT / "docs" / "RELEASE_NOTES_0.3.0.md").read_text(
        encoding="utf-8"
    )

    assert "## [0.3.0] - 2026-09-20" in changelog
    assert "First public, field-tested release." in changelog
    assert "# Release notes: 0.3.0" in release_notes
    assert "Status: published release" in release_notes
    assert "releases/tag/v0.3.0" in release_notes
    assert "94b7305c3fcb61b3647452637fb479735a66e8b7" in release_notes
    assert (
        "190b3aeb71e43fed8592242416ed5cd702bdbc9c2e82bdb279b4cea4d9209dc5"
        in release_notes
    )


def test_build_release_is_deterministic(tmp_path: Path) -> None:
    """Two builds contain the same files and produce identical bytes."""
    version = read_version()
    _write_versions(tmp_path, version, version)
    shutil.copytree(
        ROOT / INTEGRATION_RELATIVE,
        tmp_path / INTEGRATION_RELATIVE,
        dirs_exist_ok=True,
    )
    first, first_checksum = build_release(Path("dist/first"), root=tmp_path)
    second, second_checksum = build_release(tmp_path / "dist/second", root=tmp_path)

    assert first.read_bytes() == second.read_bytes()
    digest = hashlib.sha256(first.read_bytes()).hexdigest()
    assert first_checksum.read_text(encoding="utf-8") == f"{digest}  {first.name}\n"
    assert second_checksum.read_text(encoding="utf-8") == f"{digest}  {second.name}\n"

    release_names = [
        path.relative_to(tmp_path).as_posix() for path in iter_release_files(tmp_path)
    ]
    with ZipFile(first) as bundle:
        assert bundle.namelist() == release_names
        assert all("__pycache__" not in name for name in bundle.namelist())
        assert all(not name.endswith(".pyc") for name in bundle.namelist())
        assert all(
            info.date_time == (1980, 1, 1, 0, 0, 0) for info in bundle.infolist()
        )


def test_release_source_rejects_symlinks(tmp_path: Path) -> None:
    """A symlink cannot smuggle an external file into the package."""
    _write_versions(tmp_path, "0.3.0", "0.3.0")
    outside = tmp_path / "outside.txt"
    outside.write_text("private", encoding="utf-8")
    (tmp_path / INTEGRATION_RELATIVE / "linked.txt").symlink_to(outside)

    with pytest.raises(ReleaseGateError, match="must not contain symlinks"):
        list(iter_release_files(tmp_path))


@pytest.mark.parametrize(
    "directory", ["../outside", "dist/../../outside", ".git", ".", "distribution"]
)
def test_build_rejects_output_outside_dist(tmp_path: Path, directory: str) -> None:
    """CLI traversal and repository metadata paths cannot receive artifacts."""
    root = tmp_path / "repo"
    _write_versions(root, "0.3.0", "0.3.0")
    before = set(tmp_path.rglob("*"))

    with pytest.raises(ReleaseGateError, match=r"inside.*dist"):
        build_release(Path(directory), root=root)

    assert set(tmp_path.rglob("*")) == before


def test_build_rejects_absolute_external_output(tmp_path: Path) -> None:
    """An absolute CLI argument cannot bypass output containment."""
    root = tmp_path / "repo"
    _write_versions(root, "0.3.0", "0.3.0")
    outside = tmp_path / "outside"
    with pytest.raises(ReleaseGateError, match=r"inside.*dist"):
        build_release(outside, root=root)
    assert not outside.exists()


def test_build_resolves_relative_output_from_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unrelated working directory cannot redirect relative CLI output."""
    root = tmp_path / "repo"
    _write_versions(root, "0.3.0", "0.3.0")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    archive, checksum = build_release(Path("dist"), root=root)

    assert archive.parent == root / "dist"
    assert checksum.parent == root / "dist"
    assert list(elsewhere.iterdir()) == []


@pytest.mark.parametrize("nested", [False, True])
def test_build_rejects_output_directory_symlink_escape(
    tmp_path: Path, nested: bool
) -> None:
    """Both dist itself and a nested link must stay inside the repository."""
    root = tmp_path / "repo"
    _write_versions(root, "0.3.0", "0.3.0")
    outside = tmp_path / "outside"
    outside.mkdir()
    output = root / "dist"
    if nested:
        output.mkdir()
        output /= "linked"
    output.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ReleaseGateError, match=r"inside.*dist"):
        build_release(output, root=root)
    assert list(outside.iterdir()) == []


def test_build_replaces_artifact_links_without_touching_targets(tmp_path: Path) -> None:
    """Neither the ZIP nor its checksum may overwrite a linked external file."""
    root = tmp_path / "repo"
    _write_versions(root, "0.3.0", "0.3.0")
    output = root / "dist"
    output.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("keep", encoding="utf-8")
    for name in (
        "meiertobler_smartguard-0.3.0.zip",
        "meiertobler_smartguard-0.3.0.zip.sha256",
    ):
        (output / name).symlink_to(outside)

    archive, checksum = build_release(Path("dist"), root=root)

    assert outside.read_text(encoding="utf-8") == "keep"
    assert not archive.is_symlink()
    assert not checksum.is_symlink()
    assert checksum.read_text(encoding="utf-8").startswith(
        hashlib.sha256(archive.read_bytes()).hexdigest()
    )
    assert len(list(output.iterdir())) == 2
