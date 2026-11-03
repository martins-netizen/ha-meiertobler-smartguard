# Release notes: 0.7.1

Status: published release

Published on **2026-11-02 at 21:47:25 UTC** as the stable latest release.
The annotated `v0.7.1` tag points to the reviewed source below. Prefer the
existing HACS entry for updates, restart Home Assistant and retain the config
entry and entity IDs.

## Fixes since 0.7.0

- Prefill the native holiday editor with `YYYY-MM-DD HH:MM:SS`. Home
  Assistant's datetime selector splits at a space; the previous `T` separator
  could duplicate the time when edited and block the confirmation screen.
- Add the `climate.heat_pumps_air_conditioning` integration category to resolve
  the HACS catalogue-metadata warning.

The date-format regression is exercised through native options flows for both
winter and summer dates, including a time edit, instant verification and
cancellation before any gateway write. The existing explicit confirmation,
identity/source checks, DST handling and write readback remain in place.

## Compatibility and upgrade

- Home Assistant minimum remains **2026.9.0**; native CI uses **2026.10.4**.
- No runtime dependency or polling-interval change.
- With all supported modules/readings: **32 numeric/enum/timestamp sensors,
  six label sensors, six binary sensors and one mode select** (45 entities).
- Prefer updating the existing **HACS** entry and restart
  Home Assistant. Keep the config entry and registered entity IDs. Reopen the
  Configure dialog and verify both date/time fields before saving a period.
- The release changes no personal dashboard, automation, helper or heating
  parameter. The dashboard heating-curve model is separate local work.

A displayed or read-back date pair does not prove physical holiday heating.
A real period change and its return path still require separate acceptance;
lighting presence-simulation coupling remains separate HA work.

## Validation and publication evidence

Reviewed source: `93be8e6ad95f12eadbbb6a0c3a88820a4ec320e5`.
Quality, Hassfest, HACS and SonarCloud passed on that exact main commit.
The annotated `v0.7.1` tag object is
`e9c4db1603d7e966ee4b00b090275712b5c20cfb`.
Its [tagged Release Gate](https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/runs/41531211956)
completed successfully on the same source. The
[full stable release](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/tag/v0.7.1)
is published with both assets:

- `meiertobler_smartguard-0.7.1.zip`: **48,813 bytes**;
  SHA-256 `930f6fbc170897930cf400582cc387de25c437f40477bb32e0608ff81d56d16e`.
- `meiertobler_smartguard-0.7.1.zip.sha256`: **99 bytes**;
  own SHA-256 `cdebde5ff6ce2d52047fa1fbe31a2764754c31751ba3ec56148b661d4f166130`.

The publication record reports byte comparison of all **21 integration files**
with that source and verification of both downloaded assets. The public release
metadata confirms the sizes and digests above. This documentation update does
not repeat the download audit or change tags, release assets or runtime files.

## Separate HACS and live acceptance

A separate maintainer field report on **2026-11-03** reports the existing HACS
entry as installed **v0.7.1**, latest **v0.7.1**, update state **off**.
This establishes HACS distribution status on that installation; it is not a
new independent byte audit, native editor browser test or physical holiday test.

Native editor date/time rendering and a chosen physical holiday period with
its return path remain separate acceptance items. The successful private HA
presence-simulation dashboard is separate configuration, outside this release.
No physical write, new holiday plan or extra restart is required merely to
complete this publication record.
