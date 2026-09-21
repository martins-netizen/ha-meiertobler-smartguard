# Changelog

All notable changes to this project are documented in this file. The project
uses stable semantic versions for release candidates and published releases.

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
