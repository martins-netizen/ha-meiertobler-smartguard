# Changelog

All notable changes to this project are documented in this file. The project
uses stable semantic versions for release candidates and published releases.

## [Unreleased]

## [0.5.0] - 2026-10-30

Published release; see [release notes](docs/RELEASE_NOTES_0.5.0.md) for the
tagged validation and package checksums. The maintainer confirmed the HACS
update and successful operation on Home Assistant Core 2026.10.4 / OS 18.4
on 2026-10-30.

### Added

- Eight optional read-only operating entities: HK60 heating/cooling room
  targets, controller outdoor temperature and Smart Grid status, three fault
  inputs and the heating-buffer heat request. Modules and individual readings
  can fail independently without hiding the original entities.
- English/German names and Smart Grid labels; room targets remain settings
  shown as sensors, and heating demand does not claim actual heater operation.

### Changed

- Show entry-specific repairs for invalid saved hosts, unsupported devices and
  changed gateway identities; retain automatic retry for transient failures.
- Guard blueprint morning recovery with a persistent ownership helper and
  provide guided German setup. Blueprint re-import remains a separate action.
- Update the CI Python baseline and pinned validation dependencies without
  changing the runtime dependency list or the Home Assistant interpreter.

## [0.4.1] - 2026-10-23

Published documentation patch; see [release notes](docs/RELEASE_NOTES_0.4.1.md)
for publication and checksum evidence. The HACS update, new README/graphic and
all existing entities were user-confirmed on 2026-10-25.

### Documentation

- Replace the release-process-heavy README with a concise user overview,
  illustrative graphic and links to installation and technical guides.
- Keep installation instructions version-neutral across publication.
- Record the user-confirmed 0.4.0 HACS update and entity availability.
- Runtime logic is unchanged; only the integration manifest version advances.

## [0.4.0] - 2026-10-22

Published release; see [release notes](docs/RELEASE_NOTES_0.4.0.md) for integrity
and validation evidence. The HACS upgrade and entity availability were
user-confirmed; see [the upgrade record](docs/HACS_TEST_V0.4.0.md).

### Added

- Optional heating-buffer and domestic-hot-water temperatures, heater status
  indicators and operating-hour counters. Enabled modules are discovered via
  the manufacturer-documented config endpoints. Missing or malformed optional
  readings do not interrupt the existing core entities.

### Security

- Restrict release output to the repository's `dist` directory and replace
  artifact symlinks without writing to their targets.
- Require SHA-256 hashes in both CI installation workflows. Prefer wheels;
  permit only the two documented source-only test dependencies, with pinned,
  hashed build tools and automatic build-dependency fetching disabled.

### Documentation

- Record the successful Home Assistant test of all six optional measurements
  and preservation of the original entities and settings.
- Separate release-candidate validation from published-release evidence while
  retaining the immutable 0.3.0 publication record.

## [0.3.0] - 2026-09-20

First public, field-tested release.

### Added

- Redacted Home Assistant diagnostics for the config entry and current
  coordinator data.
- A guarded night-heating automation blueprint for source-controlled testing.
- Troubleshooting, automation, release-readiness, and publication guides.
- A structured privacy-conscious GitHub bug-report form.

### Changed

- Expanded the Home Assistant test foundation across setup, config flow,
  coordinator, entities, diagnostics, and release behavior.
- Enabled strict MyPy validation for the full integration and retained the
  minimum 95 percent statement and branch coverage gate.
- Added a read-only, SHA-pinned release gate that builds a deterministic ZIP
  and SHA-256 checksum without publishing them.
- Required the integration manifest, project metadata, and lock-file root
  package to carry the same stable version.

### Security

- Diagnostics redact the configured host, global device identifier, and serial
  number.
- The integration stores no credentials and has no external Python runtime
  dependency.
- The SmartGuard REST API remains unauthenticated HTTP and must stay on a
  segmented local network with restrictive access to TCP port 80.

## [0.2.0] - 2026-09-19

Private development baseline with UI configuration, eight sensors, and one
verified HK60 operating-mode select with immediate write readback.
