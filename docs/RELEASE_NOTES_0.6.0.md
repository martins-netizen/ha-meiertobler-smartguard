# Release notes: 0.6.0

Status: release candidate

This candidate is **not yet published**. The annotated `v0.6.0` tag, tagged
Release Gate and full GitHub release are pending. Check
[GitHub Releases](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/latest)
for available downloads. A live HACS update follows publication.

## Changes since 0.5.0

### HK60 flow target and controller parameters

- Current requested flow temperature, alongside the existing actual flow
  temperature. Both suggest one decimal for display without rounding stored values.
- Heating design outdoor temperature, heating/cooling outdoor on/off thresholds
  and their damping durations: nine read-only controller parameters.
- Each of the ten optional readings is discovered independently after its first
  valid response. Missing or invalid values do not replace measurements with zero
  or prevent the original readings from updating; later recovery is supported.

The current flow target is distinct from room targets and the design flow
temperature. Thresholds and damping durations describe settings, not measured
temperatures, runtime counters or a proven controller algorithm. See the
[HK60 guide](HK60_FLOW_AND_LIMITS.md) for exact datapoints, units and validation.

### Configured module names

Enabled controller, HK50/HK60/HK70, buffer and hot-water modules can supply
their configured labels as default display-name prefixes and diagnostic label
sensors. For example, a configured Floor heating label makes the HK60 readings
easier to identify. Technical module IDs remain available as attributes.

Existing registered entity IDs, unique IDs, device assignment, custom names and
precision overrides are preserved. Fresh installations may derive their initial
IDs from the configured labels. Later label changes update default names without
renaming registered IDs. Missing or invalid labels fall back to translated names;
existing label sensors become unavailable and can recover later.

HK50/HK70 discovery reads their configuration only. Numeric readings and mode
controls remain limited to the supported HK60 circuit. Free-text labels are
redacted in downloaded integration diagnostics; review files before sharing.

## Compatibility, upgrade and rollback

- Home Assistant **2026.9.0 or newer**; SmartGuard 2.0, device type `1001`.
- Keep the existing config entry, entity IDs, names and automations. Update the
  existing HACS entry and restart Home Assistant after publication.
- With all supported modules, readings and labels available: **26 numeric/enum
  sensors, up to six diagnostic label sensors, six binary sensors and one mode
  select** (39 entities). Unavailable modules/fields reduce that count.
- The coordinator retains its 60-second sequential poll. A complete refresh uses
  at most **38 GETs**, including six shared module configuration checks.
- No new gateway writes, editable temperature/duration controls or automatic
  mode changes. Existing night automations and imported blueprints are unchanged.
- This release supplies measurements for target/actual comparisons. It does not
  install a fault-monitoring automation or prove a malfunction from a brief gap.
- HACS uses the tagged integration source. The separate manual ZIP retains the
  `custom_components/meiertobler_smartguard` layout.
- To roll back, select published **0.5.0** in HACS and restart. New entities may
  become unavailable; preserve the config entry and existing automations.

## Validation and pending publication

The reviewed feature passed synthetic API, entity, translation, lifecycle and
diagnostic tests. Separate read-only field observations confirmed the flow-target
mapping and the nine parameter endpoints on one gateway. No live installation or
rendered-UI acceptance of this versioned candidate is claimed by those checks.

The exact versioned candidate passed **271 tests and 26 subtests** on Python
3.14.10 / Home Assistant 2026.10.4, with **100% integration statement and branch
coverage** (530 statements / 94 branches). Repository validation, Ruff, strict
MyPy (14 files) and dependency consistency passed. Two independent deterministic
ZIP builds agreed and all 19 members matched source bytes. These are local
candidate results, distinct from the pending publication and live HACS test.
Quality, Hassfest, HACS and SonarCloud are required on the PR head and merged
main before tagging.
The tagged Release Gate repeats the build and validations but never publishes
automatically. Publication verifies the gate artifact, checksum and both uploaded
assets. The [release checklist](RELEASE_CHECKLIST.md) records these separate steps.

## Known limitations

The local REST API uses unauthenticated HTTP and belongs on a trusted local
network. Configured labels may contain personal text and remain visible in local
HA names even though integration diagnostics redact them. Module labels are not
new heating-circuit controls. Unsupported return-temperature, controller-mode and
EVU readings remain outside this release. Heater indicators and heat requests do
not measure electrical power or energy. This independent community project is
not affiliated with or endorsed by Meier Tobler AG.
