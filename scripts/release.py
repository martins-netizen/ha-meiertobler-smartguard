#!/usr/bin/env python3
"""Verify release versions and build a deterministic integration archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from collections.abc import Iterator, Sequence
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_RELATIVE = Path("custom_components/meiertobler_smartguard")
TAG_PATTERN = re.compile(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
IGNORED_PARTS = {"__pycache__"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class ReleaseGateError(ValueError):
    """A release candidate violates a release invariant."""


def read_version(root: Path = ROOT) -> str:
    """Return the shared manifest, project, and lock-file version."""
    manifest_path = root / INTEGRATION_RELATIVE / "manifest.json"
    project_path = root / "pyproject.toml"
    lock_path = root / "uv.lock"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    with project_path.open("rb") as project_file:
        project = tomllib.load(project_file)
    with lock_path.open("rb") as lock_file:
        lock = tomllib.load(lock_file)

    manifest_version = manifest.get("version")
    project_version = project.get("project", {}).get("version")
    lock_versions = [
        package.get("version")
        for package in lock.get("package", [])
        if isinstance(package, dict)
        and package.get("name") == "ha-meiertobler-smartguard"
    ]
    if (
        not isinstance(manifest_version, str)
        or not isinstance(project_version, str)
        or len(lock_versions) != 1
        or not isinstance(lock_versions[0], str)
    ):
        raise ReleaseGateError(
            "Manifest, project, and lock versions must be unique strings"
        )
    lock_version = lock_versions[0]
    if manifest_version != project_version or manifest_version != lock_version:
        raise ReleaseGateError(
            "Manifest, project, and lock versions differ: "
            f"{manifest_version!r}, {project_version!r}, {lock_version!r}"
        )
    if TAG_PATTERN.fullmatch(f"v{manifest_version}") is None:
        raise ReleaseGateError(f"Unsupported release version: {manifest_version!r}")
    return manifest_version


def verify_tag(tag: str, root: Path = ROOT) -> str:
    """Verify that a stable release tag exactly matches the source version."""
    match = TAG_PATTERN.fullmatch(tag)
    if match is None:
        raise ReleaseGateError("Release tag must use the stable form vMAJOR.MINOR.PATCH")
    version = read_version(root)
    if tag != f"v{version}":
        raise ReleaseGateError(
            f"Release tag {tag!r} does not match source version {version!r}"
        )
    return version


def iter_release_files(root: Path = ROOT) -> Iterator[Path]:
    """Yield the integration files in deterministic archive order."""
    integration = root / INTEGRATION_RELATIVE
    if not integration.is_dir():
        raise ReleaseGateError(f"Integration directory is missing: {integration}")

    for path in sorted(integration.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            raise ReleaseGateError(f"Release source must not contain symlinks: {relative}")
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if path.suffix in IGNORED_SUFFIXES:
            continue
        if path.is_file():
            yield path


def build_release(
    output_directory: Path,
    root: Path = ROOT,
) -> tuple[Path, Path]:
    """Build the deterministic integration ZIP and its SHA-256 checksum."""
    version = read_version(root)
    output_directory.mkdir(parents=True, exist_ok=True)
    archive = output_directory / f"meiertobler_smartguard-{version}.zip"
    checksum = archive.with_suffix(".zip.sha256")

    files = list(iter_release_files(root))
    if not files:
        raise ReleaseGateError("Release source contains no files")

    with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in files:
            relative = path.relative_to(root).as_posix()
            info = ZipInfo(relative, date_time=ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes(), compresslevel=9)

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return archive, checksum


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="check source version invariants")

    verify_parser = subparsers.add_parser("verify-tag", help="verify a release tag")
    verify_parser.add_argument("--tag", required=True)

    build_parser = subparsers.add_parser("build", help="build release artifacts")
    build_parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("dist"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selected release-gate command."""
    args = _parser().parse_args(argv)
    if args.command == "check":
        version = read_version()
        print(f"Release version: {version}")
    elif args.command == "verify-tag":
        version = verify_tag(args.tag)
        print(f"Release tag verified: v{version}")
    else:
        archive, checksum = build_release(args.output_directory)
        print(f"Release archive: {archive}")
        print(f"Checksum: {checksum}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
