# Release notes: 0.4.0

Status: published release

[Version 0.4.0](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/tag/v0.4.0)
was published as a full, latest GitHub release on 2026-10-22. Its
annotated `v0.4.0` tag and Release Gate were verified before publication.

## Changes from 0.3.0

- Optional heating-buffer and domestic-hot-water temperatures.
- Two heater indicators reported by SmartGuard and two diagnostic operating-hour
  counters. Zero hours and inactive indicators are valid readings.
- Module discovery and isolated handling of unavailable or malformed optional
  readings. Existing core entities continue updating when an optional value fails.
- Release output constrained to `dist`, including protection against directory
  symlink escapes and writes through existing artifact symlinks.
- Hash-checked CI dependencies and pinned build tools in both workflows, with
  only the documented source-only test dependencies permitted to build.

With both storage modules enabled and returning valid data, the integration
provides **12 sensors, two binary sensors and one HK60 mode select**. The eight
original sensors, device identity, existing unique IDs, 60-second poll interval
and verified HK60 write/readback behavior are preserved. No heater controls or
setpoint changes are added. Indicators report gateway status; they are not
electrical power or energy meters.

## Compatibility and upgrade

- Home Assistant **2026.9.0 or newer**, unchanged from 0.3.0.
- SmartGuard 2.0, device type `1001`; HK60 must be enabled for HK60 entities.
- Buffer and hot-water modules are optional. Their entities appear after their
  first valid readings; unavailable modules do not block the original entities.
- No new runtime dependency, configuration migration or entity renaming.

Use the existing HACS entry to update to 0.4.0 and restart
Home Assistant. Keep the existing config entry; do not remove and recreate the
integration. Confirm the existing entities and any supported additional values.
Operating-hour counters are diagnostic entities and may appear in that section.

HACS installs the tagged `custom_components/meiertobler_smartguard` tree.
The deterministic ZIP and checksum are separate manual-installation assets.
For rollback, use a verified backup or select the previous published HACS
version and restart; extra measurement entities will then cease to provide data.

## Verification and remaining gates

The feature source passed a real Home Assistant installation check: source
bytes, all 15 entities, existing IDs/settings and protected configuration were
verified. Temperature and inactive-indicator displays were confirmed. The
original mode select and guarded night automation have prior field evidence.
See [Additional measurements](ADDITIONAL_MEASUREMENTS.md) for the anonymized
feature result. The subsequent user-confirmed HACS upgrade is recorded separately in
[HACS_TEST_V0.4.0.md](HACS_TEST_V0.4.0.md).

Release PR #24 and README PR #25 were merged through the protected branch.
Quality, Hassfest, HACS and SonarCloud passed on source commit
`02b7cff7869a642b2191d3877e19f211cc72a35f`. The tagged
[Release Gate](https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/runs/39843987656)
passed repository validation, Ruff, strict MyPy and the regression suite.

The 18 integration files in the downloaded bundle were verified byte for byte
against the tagged source. The two uploaded release assets, public release and
latest-release status were verified after publication at 20:01:41 UTC.
The maintainer confirmed the HACS update to 0.4.0 and existing entity
availability on 2026-10-23. The starting installation already contained the
storage feature. No new independent source-byte, registry or separate restart
verification is claimed; see the [upgrade record](HACS_TEST_V0.4.0.md).

## Integrity

Source commit: `02b7cff7869a642b2191d3877e19f211cc72a35f`.
Annotated tag object: `db9198f50e5b35e920e895c1cf0c6e6d45d4ffd8`.

Manual bundle: `meiertobler_smartguard-0.4.0.zip` (18 integration files).
SHA-256 `9b856d6c16bb023262992da7a9528a71cdc231ce92abe7e4e54daea3182bb4b2`.
The attached `.zip.sha256` file contains the same checksum. GitHub-generated
source archives are distinct from this manual-installation bundle; HACS uses
the tagged integration source tree.

## Known limitations

The local SmartGuard API uses unauthenticated HTTP. Restrict access to the
trusted local Home Assistant network; the gateway UI password does not secure
the REST API. Device types other than `1001`, automatic discovery and repair
issues remain unsupported. This release does not add room-control support or
change heating, cooling, hot-water targets or existing automations.
