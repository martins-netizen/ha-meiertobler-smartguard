# Release notes: 0.4.1

Status: published release

[Version 0.4.1](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/tag/v0.4.1)
was published as a full stable release on **2026-10-23 at 05:40:13 UTC**.
The maintainer confirmed the HACS update, new README/graphic and availability
of all 15 existing entities on **2026-10-25**. This is user-reported update/UI
evidence, not a new independent file audit.

## Changes

- Shorter README organised around features, installation, updates and safety.
- Existing community icon in an illustrative feature graphic and linked HACS,
  release and validation badges.
- Detailed installation/recovery and technical/development reference guides.
- Version-neutral README instructions and the user-confirmed 0.4.0 HACS record.

Runtime logic is unchanged from 0.4.0; only the manifest version changes.
With both storage modules providing valid data, this release has 12 sensors,
two binary sensors and one HK60 mode select. No new entities, integration
runtime dependencies, settings or controls were introduced in 0.4.1.

## Source and integrity

The current annotated `v0.4.1` tag resolves to source commit
`094845ea561b3d23ccf26bc9fea0913de68a5b5d`. Its
[Release Gate](https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/runs/40373063287)
passed on 2026-10-26 after repository metadata maintenance. That revalidation is
separate from the original 2026-10-23 publication; the originally published
assets remain unchanged.

- Archive: `meiertobler_smartguard-0.4.1.zip`, 34,045 bytes.
- ZIP SHA-256 `bbc4734035a05897faa24063822a3da9a06d7a7e346abdb155e10121e4ffba22`.
- The attached `.zip.sha256` contains that ZIP checksum.

HACS installs the tagged integration source tree. The attached ZIP is a separate
manual-installation bundle. GitHub's automatic source archives have different
checksums. Existing release tags and assets are not moved to update this guide.

## Compatibility and update

Home Assistant **2026.9.0 or newer**, SmartGuard 2.0 device type `1001`.
Use the existing HACS entry, restart Home Assistant and retain the config entry,
entity IDs, settings and automations. No new physical operating-mode cycle was
needed for this documentation patch. For rollback, select 0.4.0 and restart.

## Validation scope and limitations

Quality, Hassfest, HACS and SonarCloud passed for the publication source; the
tagged bundle was verified before publication. The earlier 0.4.0 HACS record
and the later user-confirmed 0.4.1 update are separate results. A clean install
on the minimum supported HA version is not claimed.

The gateway REST API uses unauthenticated HTTP and belongs on a trusted local
network. Heater indicators report gateway status, not electrical power or
energy. This release adds no heater controls, editable temperature targets,
automatic discovery or repair notices. Later source changes are described in
their own release notes, not retroactively assigned to 0.4.1.
