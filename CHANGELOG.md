# Changelog

All notable changes to this project are documented in this file. The project
uses stable semantic versions for release candidates and published releases.

## [Unreleased]

### Changed

- Require Home Assistant Core 2026.11.0 or newer. Update Core before installing
  a SmartGuard release with this requirement. SmartGuard 0.7.2 supports HA
  2026.9 and 2026.10.

### Security

- Use a Core baseline with updated Pillow, aiohttp, PyJWT, cryptography and uv
  versions to address known vulnerabilities in the previously supported Core
  releases.
- Require multidict 6.9.1 or newer in CI and the Release Gate for CVE-2026-104874.

## [0.7.2] - 2026-11-08

Source-preparation record; publication is a separate gated step. See the
[0.7.2 preparation notes](docs/RELEASE_NOTES_0.7.2.md) and
[GitHub Releases](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/latest)
for current availability.

### Changed

- Default the two diagnostic heater operating-hour counters to disabled only
  for newly created entity-registry entries. Preserve existing activation,
  custom IDs and names; storage readings and gateway polling remain unchanged.
- Run the complete suite on HA 2026.11.0 and the supported minimum HA 2026.9.0
  in isolated, hash-pinned environments. The protected Quality check requires
  both. Use the official `pytest-homeassistant` plugin for current HA.

### Documentation

- Document Marketplace installation and updates on HA 2026.11+, retaining the
  HACS route for older HA.
- Distinguish the stable release, development changes and separate Home
  Assistant orchestration; refresh the user and development guides.
- Keep the README valid across publication by linking to the current release
  instead of embedding temporary candidate or latest-version claims. Explain
  that Marketplace documentation comes from the installed version.

## [0.7.1] - 2026-11-02

Published stable release; see [0.7.1 release notes](docs/RELEASE_NOTES_0.7.1.md)
for the source, tagged Release Gate and asset checksums. A separate maintainer
field report on 2026-11-03 confirms HACS installed/latest 0.7.1. Physical
holiday operation and native editor browser acceptance remain separate.

### Fixed

- Format prefilled holiday dates with the space separator expected by Home
  Assistant's datetime selector. Editing a time no longer duplicates it or
  prevents the review-and-confirm step.

### Changed

- Classify SmartGuard under heat pumps and air conditioning in integration
  catalogue metadata, resolving the HACS missing-category warning.

## [0.7.0] - 2026-11-02

Published stable release. Tag, tagged Release Gate and assets are verified;
see [0.7.0 notes](docs/RELEASE_NOTES_0.7.0.md). A post-release technical check
confirmed all 21 installed files; HACS-path/UI and physical holiday acceptance
are separate evidence.

### Added

- A guided HK60 whole-period holiday editor: choose both dates, review the
  circuit, old/new and intermediate periods, then explicitly confirm. Source
  checks, expiring confirmation and full readback guard each write. Partial or
  unknown results stop without automatic retry or blind rollback. Physical
  holiday operation remains unverified; lighting coupling is separate HA work.
- Two optional read-only holiday start/end timestamp sensors using whole UTC
  Unix seconds and HA's local display. Invalid or unconfirmed zero values remain
  unavailable. Downloaded integration diagnostics redact both holiday times.
- Four optional read-only heating-curve diagnostics: heating boost in kelvin,
  design flow and minimum normal/reduced flow. No editable temperature setpoints.
- A plan retaining both independently scheduled holidays and an additional
  >24-hour absence suggestion with a requested end time.

### Changed

- Put the HK60 measurement first with a short circuit suffix, keeping configured
  assignments in module metadata. Describe the outdoor reading as an outdoor
  temperature sensor. Preserve registered IDs, device assignment, custom names
  and display settings.
- Refuse HTTP redirects for gateway requests. Keep the existing verified mode
  controls and share their local write lock with confirmed holiday changes.

## [0.6.0] - 2026-11-01

Published stable release; see [release notes](docs/RELEASE_NOTES_0.6.0.md) for
the source, tagged validation and package checksums. A separate technical installation check verified all 19 release files on
2026-11-01; HACS/UI acceptance remains a distinct pending step.

### Added

- Ten optional read-only HK60 sensors: current flow target temperature,
  heating design outdoor temperature, heating/cooling outdoor thresholds and
  their on/off damping durations. Each value can fail and recover independently.
- Configured circuit/storage labels in display names and module attributes,
  plus up to six diagnostic label sensors for the controller, HK50/HK60/HK70,
  buffer and hot water. Existing IDs and user names remain; free-text module
  labels are redacted in integration diagnostics.
- English/German names and one-decimal suggested precision for the flow target
  and existing actual flow temperature, preserving full numeric values and
  personal display settings. No new gateway controls.

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
