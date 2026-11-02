# Release notes: 0.7.1

Status: release candidate

Version 0.7.1 is not yet published. The latest stable HACS release remains
[0.7.0](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/tag/v0.7.0).
The annotated `v0.7.1` tag, its successful Release Gate, verified assets and
explicit stable full-release publication remain separate steps.

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
- After publication, prefer updating the existing **HACS** entry and restart
  Home Assistant. Keep the config entry and registered entity IDs. Reopen the
  Configure dialog and verify both date/time fields before saving a period.
- The release changes no personal dashboard, automation, helper or heating
  parameter. The dashboard heating-curve model is separate local work.

A displayed or read-back date pair does not prove physical holiday heating.
A real period change and its return path still require separate acceptance;
lighting presence-simulation coupling remains separate HA work.

## Validation and remaining publication steps

The two reviewed fixes are merged on main with four successful checks. The
versioned release candidate must pass Quality, Hassfest, HACS and SonarCloud.
After approval, verify the actual merged commit, create the annotated tag,
wait for that tag's Release Gate, and compare both uploaded/downloaded assets
with the source before publishing the stable full release. Record the final
source, gate and checksums after publication, without rewriting previous tags.
