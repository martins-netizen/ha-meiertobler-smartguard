# Release notes: 0.5.0

Status: release candidate

This candidate is **not yet published**. The annotated `v0.5.0` tag, tagged
Release Gate and full GitHub release are still pending. Use
[GitHub Releases](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/latest)
to find the currently available stable version. This preparation does not
install anything in Home Assistant.

## Changes since 0.4.1

### Eight additional read-only entities

- HK60 room heating and cooling targets, displayed as settings in °C.
- Controller outdoor temperature and Smart Grid status.
- Heat-generator fault input and priority 1/2 collective fault inputs.
- Heating-buffer heat request, distinct from actual heater operation.

These readings are optional and appear after their first valid response.
Missing modules or individual values do not interrupt the original readings;
an unavailable fault input is not silently shown as clear. False and zero are
valid results. With every supported module returning valid readings, there are
**16 sensors, six binary sensors and one HK60 mode select**. See
[operating readings](OPERATING_READINGS.md) for paths, units and interpretation.

### Actionable configuration repairs

An invalid saved host, a confirmed unsupported device or a different gateway
identity stops setup and creates an English/German repair notice. A different
gateway is rejected before further measurements or control setup. Notices link
to the existing reconfiguration UI, clear after successful identity verification
and are scoped to the affected entry. Timeouts and ambiguous responses retain
automatic retries. No automatic gateway or address change is performed.

Identity verification happens during setup/reload, not on every normal poll.
Legacy entries without a saved unique identity are not falsely treated as a
confirmed mismatch. See [troubleshooting](TROUBLESHOOTING.md).

### Guarded night-heating blueprint

The blueprint uses a separate persistent ownership helper for morning recovery.
It only returns Heating to Auto when it owns the override; confirmed manual
changes to another mode clear ownership. German setup sections explain both
helpers, entity selection and optional times.

HACS integration updates **do not re-import blueprints or replace saved
automations**. Existing production automations continue independently. If you
separately re-import this blueprint, provide distinct enable/ownership helpers
and review [setup and limitations](AUTOMATION_EXAMPLES.md). Identical-value or
unobserved manual selections cannot be distinguished, and missed morning
triggers have no startup/reconnection catch-up.

### Validation maintenance

The CI Python baseline and pinned build/test dependencies were updated,
including transport-security fixes. Existing hash checks, universal dependency
markers and separate HACS/Hassfest validation remain. Updating this integration
does not update Home Assistant's bundled Python or the host operating system.

## Compatibility and upgrade

- Home Assistant **2026.9.0 or newer**; SmartGuard 2.0, device type `1001`.
- Keep the existing config entry, entity IDs, names, settings and automations.
- After publication, update through the existing HACS entry and restart Home
  Assistant. Optional entities appear when their modules provide valid values.
- Confirm the original entities and the available additional readings. A new
  physical mode-switch cycle or artificial fault is not needed for this check.
- HACS uses the tagged integration source. The separately built manual ZIP
  retains the `custom_components/meiertobler_smartguard` layout.
- For rollback, select published 0.4.1 in HACS and restart. The additional
  operating entities may become unavailable on the older version.

The 60-second coordinator interval and existing mode write/readback behavior are
retained. All supported optional readings use at most **26 sequential GETs** per
complete refresh. Room targets remain read-only; there are no new heating-curve,
EVU/Smart Grid command or electric-heater controls.

## Validation and remaining steps

The complete versioned candidate passed the full automated suite on Python 3.14.10 and
Home Assistant 2026.10.4: **209 tests and 26 subtests**, with **100% integration
statement and branch coverage** (487 statements / 82 branches). Repository
validation, Ruff, strict MyPy and dependency consistency passed. Two independent
local ZIP builds were identical and all 19 integration files matched the source
bytes. These local results do not replace the still-pending tagged Release Gate.

The selected eight datapoints were confirmed by a separate read-only gateway
inventory. That is not an installation test of this release. A clean install on
the minimum HA version, rendered repair UI and a new live blueprint migration
are not claimed. Existing night-switching and earlier HACS update evidence
remain historical results and need not be repeated for unchanged behavior.

PR/main checks, the annotated tag, tagged Release Gate, explicit publication,
and the actual HACS update/availability check are recorded separately in the
[release checklist](RELEASE_CHECKLIST.md). No final release checksum is claimed
before the tagged bundle is selected and verified.

## Known limitations

The local REST API uses unauthenticated HTTP; restrict it to a trusted local
network. Diagnostic identifiers are redacted, but review files before sharing.
Heater indicators and heat requests do not measure electrical power or energy.
The invalid return-temperature reading, rejected controller operating-mode
endpoint and inconsistent EVU-status type are not exposed by this release.
Automatic discovery, unsupported device types and automatic repair actions
remain outside the implemented scope. This independent community project is
not affiliated with or endorsed by Meier Tobler AG.
