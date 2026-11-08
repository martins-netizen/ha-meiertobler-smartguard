# Release notes: 0.7.2

Status: release candidate

This file records source preparation. At this checkpoint the candidate is
**not yet published**. The annotated `v0.7.2` tag, tagged Release Gate and
publication assets are later, separately authorized steps. For current
availability use [GitHub Releases](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/latest).

## Changes since 0.7.1

- Ship a README that stays accurate across publication. Marketplace reads the
  README at the installed version or commit; a documentation-only merge on
  `main` cannot replace the old file inside the immutable 0.7.1 tag. This
  version removes temporary candidate/latest-version claims from the overview.
- Default the two diagnostic heater operating-hour counters to disabled only
  when first registered, as reviewed in PR #53. Existing enabled/disabled
  choices, IDs and names are retained. Optional reading and polling continue.
- Include the complete current/minimum HA test matrix from PR #52 and the
  refreshed user/developer guides from PR #54. Both complete suites must pass
  the protected Quality check.

## Compatibility and update

- Minimum HA remains **2026.9.0**; CI covers **2026.11.0** and **2026.9.0**.
- Up to 45 supported entities and 44 coordinated GETs per 60-second refresh.
- After publication, update the existing Marketplace/HACS entry and restart
  Home Assistant. Keep the existing config entry and registered entity IDs.
- Publication alone does not update the files or README of an installation
  that still reports 0.7.1. Check the installed version and the Marketplace
  README separately after updating.
- The counter default does not change an existing registry entry. No heater
  control, temperature-setpoint control, iDM dependency or adaptive preheating
  is added. Existing mode and confirmed holiday writes retain their guards.

Physical holiday effect remains separate from successful stored-date readback.
Private calendars, dashboards and presence simulation remain outside this
integration. Existing field acceptance is retained for its unchanged scope.

## Required validation and publication gates

The source preparation starts from reviewed main
`6579b0c6a08f5b5739569e67f2cbd90e67812e95`. Only the manifest version changes
inside the integration relative to that main; all other integration files must
remain byte-identical. Release metadata and version assertions advance together.

Before publication, require both full HA suites, repository and release checks,
Ruff, strict MyPy, Hassfest, HACS and SonarQube analysis on the exact PR head,
then verify the actual merge checks. The tagged Release Gate must build a
deterministic ZIP and SHA-256 file; compare all 21 integration files against
the selected source and verify both uploaded assets before reporting release
success. No tag, GitHub release, HA update or restart is created by this record.
