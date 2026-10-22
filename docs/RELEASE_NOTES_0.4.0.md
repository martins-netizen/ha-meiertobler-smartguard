# Release notes: 0.4.0

Status: release candidate

This candidate is not yet published. The planned annotated `v0.4.0` tag,
tagged Release Gate and full GitHub release remain pending. The latest
published release is [0.3.0](RELEASE_NOTES_0.3.0.md).

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

After publication, use the existing HACS entry to update to 0.4.0 and restart
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
feature result. These checks do not claim a new HACS release upgrade test.

Repository validation, Ruff, strict MyPy, regression tests and deterministic
local bundle checks are required for this candidate. Successful PR and final
`main` checks, the annotated-tag Release Gate, bundle inspection, explicit
publication and the HACS 0.3.0-to-0.4.0 update check are recorded separately in
the [release checklist](RELEASE_CHECKLIST.md).

## Known limitations

The local SmartGuard API uses unauthenticated HTTP. Restrict access to the
trusted local Home Assistant network; the gateway UI password does not secure
the REST API. Device types other than `1001`, automatic discovery and repair
issues remain unsupported. This release does not add room-control support or
change heating, cooling, hot-water targets or existing automations.
