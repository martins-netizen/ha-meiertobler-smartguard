# Release notes: 0.8.0

Status: release candidate

This file records source preparation; the candidate is **not yet published**.
The annotated `v0.8.0` tag, tagged Release Gate and publication assets are
separate steps after review of the exact merged source. Check
[GitHub Releases](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/latest)
for current availability; this record does not change an installed version.

## Changes since 0.7.2

- Add the response-only
  `meiertobler_smartguard.get_write_capabilities` action. Automations can find
  the enabled HK60 operating-mode select for one configured gateway, its
  internal options and current availability. Renamed entity IDs are respected.
  See the [response contract and YAML example](AUTOMATION_EXAMPLES.md#discover-write-capabilities).
- Require Home Assistant Core **2026.11.0 or newer**. Previously supported Core
  versions shipped dependency versions with known vulnerabilities. Upgrade
  Core before installing 0.8.0; keeping 0.7.2 does not repair Core dependencies.
- Maintain validation dependencies in one native universal uv project under
  `ci/`, with hash-checked installation and the reviewed HA fixture binding.
  The relocation from `.github/` was followed by a real Dependabot update PR;
  the internal GitHub rejection rule remains unknown. Include the reviewed
  mypy 2.4.1, pip 26.3, Ruff 0.17.4 and ast-serialize 0.13.1 lock updates.
- Separately require **multidict 6.9.1 or newer** in CI and the Release Gate for
  CVE-2026-104874. This is a validation-environment constraint; the integration
  does not install or override Home Assistant's runtime dependencies.

Version 0.8.0 identifies the additive catalogue and the raised Core minimum.
The already published 0.7.2 source, tag and assets remain unchanged.

## Architecture and security scope

The catalogue reads Home Assistant's local entity registry and state; calling
it causes no gateway HTTP request or write. User calls require read access to
the returned select and a loaded, explicitly selected SmartGuard entry.
An absent or disabled select returns an empty parameter mapping; an unavailable
select is described with `available: false`.

The response describes the existing HK60 mode control only. It is not a raw
gateway parameter browser or permission to invoke a returned action. Mode
changes still use `select.select_option`, its control permission, allowlisted
options and immediate gateway readback. The separately confirmed holiday
editor retains its source, identity, expiry and readback checks. No arbitrary
datapoint writes, new heater controls or editable temperature setpoints are
introduced.

The gateway's unauthenticated local HTTP API still requires a trusted,
restricted network. This version does not add gateway authentication or TLS.
The [security policy](../SECURITY.md) and existing network restriction apply.

## Compatibility and update

- SmartGuard 2.0, device type `1001`; HK60 enabled for its entities.
- Core **2026.11.0 or newer**. SmartGuard 0.7.2 remains compatible with Core
  2026.9/2026.10, as historical compatibility rather than a security-update
  recommendation. The complete suite uses the matching HA 2026.11.0 fixture.
- Up to **45 entities** and **44 coordinated GETs** per 60-second refresh;
  the local catalogue adds neither an entity nor an additional gateway poll.
- Once published, update the existing Marketplace entry and restart HA. Keep
  the existing config entry, IDs, names, saved activation and automations.
  No config-entry migration or entity recreation is required from 0.7.2.
- Existing automations do not need the catalogue. Add its response action
  explicitly where discovery is useful; only a separate chosen control action
  can change a mode. Blueprints are imported separately and are not replaced
  by this integration update.

Private calendars, dashboards, presence simulation and adaptive preheating
remain separate HA configuration. Physical holiday operation and automatic
gateway discovery are not established by this release preparation.

## Source validation and publication gates

Preparation starts from reviewed main
`39a0af1a7b2960f383067f73e324246117b86867`, including merged PRs #56–#60.
Relative to that source, only the manifest version changes inside the
integration. All other integration files, the blueprint, `ci/` manifest/lock,
workflow permissions, action pins, platform markers, hashes and quality gates
must remain byte-identical. Root release metadata and the existing version
assertions advance together; user and maintenance guides describe this scope.

Require repository/release validation, dependency consistency, Ruff, strict
MyPy and the complete suite with statement/branch coverage. Require successful
Tests (Current HA), Quality, Hassfest, HACS and SonarQube analysis on the exact
PR head, then independently verify the actual merge checks. Known upstream
deprecation warnings remain visible. The quality checklist remains a custom
integration self-assessment, not official Gold certification.

Before publication, the annotated tag's read-only Release Gate must build the
deterministic ZIP and checksum. Compare every integration member byte for byte
with the selected source and download/verify both publication assets. Keep the
tagged result and any later HA installation/field acceptance distinct from
local source checks. No tag, release or HA operation is performed by this record.
