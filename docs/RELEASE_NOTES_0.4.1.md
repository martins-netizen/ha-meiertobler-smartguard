# Release notes: 0.4.1

Status: release candidate

This documentation patch is not yet published. An annotated `v0.4.1` tag,
successful tagged Release Gate, bundle inspection and explicit publication are
required before it becomes available as a HACS release.

## Changes

- Shorter README organised around features, installation, updates and safety.
- Existing community icon in an illustrative feature graphic and three linked
  badges for HACS, the latest release and validation.
- Detailed installation/recovery and technical/development reference guides.
- Version-neutral README instructions so tagged snapshots do not retain stale
  candidate or latest-version claims after publication.
- Record the user-confirmed 0.4.0 HACS update and entity availability.

## Compatibility and upgrade

Home Assistant **2026.9.0 or newer**, SmartGuard 2.0 device type `1001`.
Runtime logic is unchanged from published 0.4.0; only the integration's manifest
version changes. There are no new entities, dependencies, settings or writes.
The existing 12 sensors, two binary sensors and one HK60 select remain available
when both optional storage modules supply valid readings.

After publication, update through the existing HACS entry and restart Home
Assistant. Keep the config entry, entity IDs, settings and automations. No
physical operating-mode change is needed for this documentation patch.
Existing published tags and assets remain untouched.

## Validation and remaining steps

The complete local suite, repository validator, Ruff, strict MyPy, deterministic
bundle and documentation/image checks are required. PR and final main checks,
tagged Release Gate, full publication and HACS rendering of the new README are
tracked separately in the [release checklist](RELEASE_CHECKLIST.md).
The [0.4.0 upgrade record](HACS_TEST_V0.4.0.md) is user-confirmed evidence for
that published release, not a claim that 0.4.1 has been installed.

## Known limitations

The local gateway REST API uses unauthenticated HTTP. Restrict access to a
trusted local network. Heater indicators report gateway status, not electrical
power or energy; this patch adds no heater controls or setpoints. Unsupported
device types, automatic discovery and repair issues remain out of scope.
