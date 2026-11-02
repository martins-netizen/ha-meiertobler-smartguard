# Release notes: 0.7.0

Status: published release

Published on **2026-11-02 at 05:42:07 UTC** as the stable latest release.
The annotated `v0.7.0` tag points to the reviewed release source. Prefer HACS
for updates and restart Home Assistant. A separate technical report verified
all **21 installed integration files** on 2026-11-02. The file check does not
establish the download path or physical holiday operation.

## Changes since 0.6.0

### Shorter names and additional read-only settings

- Put the measurement first with a short HK60 suffix, for example **Flow target
  · HK60** / **Vorlauf SOLL · HK60**. Keep configured assignments separately as
  **HK60: Example floor circuit**. The outdoor reading is named **Outdoor
  temperature sensor** / **Aussentemperaturfühler**.
- Add four optional diagnostic settings: heating boost (`5071`, temperature
  difference in K), design flow (`5222`) and minimum normal/reduced flow
  (`5223`/`5225`). They are read-only sensors without measurement statistics.
- Add optional holiday start/end timestamp sensors (`5226`/`5227`). Strict
  positive whole Unix seconds are converted to UTC-aware instants; HA handles
  local display. Missing, invalid or unverified zero values stay unavailable.
  Exact holiday times are redacted in integration diagnostics.

Existing entity/unique IDs, gateway assignment, user names and precision
settings are preserved. Invalid optional readings fail and recover independently.
See [heating-curve diagnostics](HK60_HEATING_CURVE.md) and
[the HK60 naming guide](HK60_FLOW_AND_LIMITS.md).

### Explicitly confirmed holiday period editing

The native **Configure** dialog collects the whole period, then shows the
verified circuit, selected mode, previous/new dates and exact intermediate
period. Saving requires a fresh explicit confirmation, valid for five minutes.
The client rechecks gateway identity, enabled circuit, mode, label and unchanged
source dates inside the existing shared write lock. It accepts only ordered
whole-second dates with an end still in the future. DST gaps and repeated local
times without a clear offset are rejected.

The gateway stores start and end independently. The order preserves start < end,
but a temporary period can affect heating immediately; this is warned about
before confirmation. After each POST, the entire period and context are read
back. Partial or unknown outcomes stop without automatic retry or blind
rollback. A lost reply succeeds only after independent confirmation of the
entire requested state. Requests do not follow redirects.

**Stored-date readback does not prove active holiday heating.** Physical writes,
activation boundaries and the reference/effect of the displayed K reduction
have not been accepted on a live gateway. Conflict checks are best effort; the
gateway has no compare-and-set or atomic transaction. Unknown unset values are
not cleared or overwritten. See [the complete contract](HOLIDAY_MODE_PLAN.md).

The editor does not change room/flow targets, the selected mode or heater
functions. Temperature settings remain read-only. Lighting presence simulation
and the additional >24-hour absence suggestion remain separate HA work; the
independently planned holiday path is retained in that design.

## Compatibility, installation and recovery

- Home Assistant **2026.9.0 or newer**, SmartGuard 2.0 type `1001`, enabled HK60.
  Native tests use Core 2026.10.4; a fresh minimum-version installation is unclaimed.
- No additional runtime dependency or change to the 60-second coordinator.
- With all supported modules/readings: **32 numeric/enum/timestamp sensors,
  six label sensors, six binary sensors and one mode select** (45 entities).
  The complete refresh uses **44 GETs**: eight core, six config and 30 optional.
  The editor performs additional requests only when used, not extra background polls.
- After publication, update the existing HACS entry and restart HA. Keep the
  config entry and existing IDs, helpers, automations and blueprints. Updates
  do not automatically re-import a blueprint or install presence/fault automations.
- Roll back integration files to published **0.6.0** if needed and restart.
  New entities may become unavailable. A file downgrade does **not** restore
  dates already stored in the gateway. Retain the previous full period before
  the first physical holiday test and review any corrective write explicitly.
- HACS uses tagged integration source; the manual ZIP preserves
  `custom_components/meiertobler_smartguard`. No tag or prior asset is changed.

## Validation

The versioned candidate passed **430 tests and 26 subtests** on Python 3.14.10 /
Home Assistant 2026.10.4, with **100% integration statement and branch coverage**
(762 statements / 166 branches). Repository validation, Ruff, strict MyPy
(16 source files) and prospective tag/version verification passed. API tests use
synthetic replies; options-flow tests use native HA. Neither is a physical
holiday write or real-browser acceptance.

The runtime comes from reviewed PRs #40–#43, merged through source
`bbf86a1cea373d61ed600b162d07ba23f48904ec`. Apart from the manifest version,
all 20 other integration files are byte-identical to that source. No dependency,
workflow, automation or runtime logic is changed by this version preparation.

Two independent deterministic ZIP builds were identical. All **21 members**
matched their source bytes. Deterministic release files:

- `meiertobler_smartguard-0.7.0.zip`: **48,745 bytes**;
  SHA-256 `a7532b182e3a639149a6a1c31a18cf0aded9942d6ccb485103194ea60b9d7e3f`.
- `meiertobler_smartguard-0.7.0.zip.sha256`: **99 bytes**;
  own SHA-256 `79f02a97ff742d0fb68ec0156b48f6252a588041d097998d509d47479e49f2c3`.

The tagged Release Gate and public asset metadata confirm these sizes and
digests. Source: `1cb5494caea9a6d8d6141d477bf3f49f5a84583d`; annotated tag
object: `4ebe3d88bbadef551c605f6500a4643c85030d4c`. The
[tagged Release Gate](https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/runs/41395371529)
passed on this exact source. Both assets are in the [full release](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/tag/v0.7.0).
Earlier tags and assets remain unchanged.

## Publication and live acceptance

PR #44, four final-main checks, the annotated tag, tagged Release Gate and
publication are complete; see the [release checklist](RELEASE_CHECKLIST.md).
The separate installed-file check is recorded above; HACS-path, rendered editor
and physical holiday acceptance remain separate. Keep the
previous known-good installation and a verified backup. A physical holiday test
requires a separately chosen, concretely confirmed period and reviewed return
path; do not exercise writes automatically during release/install checks.

The exact controller heating curve and any direct wind input remain unverified.
Heating on/off damping settings do not prove a curve-averaging window. Do not
interpret a simple model/target difference as a heating fault. The local API is
unauthenticated HTTP and belongs on a restricted trusted network. This is an
independent community integration without manufacturer endorsement.
