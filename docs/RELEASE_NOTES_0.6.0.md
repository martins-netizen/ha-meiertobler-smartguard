# Release notes: 0.6.0

Status: published release

[Version 0.6.0](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/tag/v0.6.0)
was published as a full stable release on **2026-11-01 at 11:03:54 UTC**.
The annotated `v0.6.0` tag, tagged Release Gate and both verified assets are
complete. A separate technical installation check on 2026-11-01 verified all
19 installed integration files against this release. The HACS update path and
rendered-UI/configured-name acceptance remain distinct pending checks.

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

## Validation and publication record

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
Release PR [#38](https://github.com/martins-netizen/ha-meiertobler-smartguard/pull/38)
passed Quality, Hassfest, HACS and SonarCloud on head
`34977068c4562da900e7d3aafcec1a65a41febd3` and after its squash merge as
`1b64e1e83e49a70b21fc025de09ee62eac6ec924`. The exact
[main Validate run](https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/runs/41298470481)
and [tagged Release Gate](https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/runs/41299829242)
completed successfully. Annotated tag object
`5da0707fc126e241555fcc8ca70e94eeb7964809` targets that same merged source.

The first publisher run stopped on a network error after creating the correct
tag. Its successful rerun reused that tag, verified the completed gate, compared
all 19 ZIP members with source, downloaded both uploaded assets again and
published explicitly. The read-only tag workflow did not publish automatically.
Release ID: `430524927`; no draft or prerelease. Integration tree:
`30e4259ab3e87365c93de02a6380b185859fb9f0`.

### Release files and integrity

- `meiertobler_smartguard-0.6.0.zip`: **39,421 bytes**, 19 integration files;
  SHA-256 `339623147f11bb719da3894f44804ed2c64700ec999154444490fbfb7419e520`.
- `meiertobler_smartguard-0.6.0.zip.sha256`: **99 bytes**, containing the exact
  ZIP digest and filename; the checksum file's own SHA-256 is
  `7bfa167f07490e36d064c4522bffde89196bcb3e8bedb2e2e529fd1b52c543a4`.

The immutable tagged notes describe the candidate before publication. These
current notes and the public GitHub release record its subsequent completion.
HACS uses the tagged source rather than the attached manual ZIP. The
[release checklist](RELEASE_CHECKLIST.md) retains the distinct live-upgrade step.

## Known limitations

The local REST API uses unauthenticated HTTP and belongs on a trusted local
network. Configured labels may contain personal text and remain visible in local
HA names even though integration diagnostics redact them. Module labels are not
new heating-circuit controls. Unsupported return-temperature, controller-mode and
EVU readings remain outside this release. Heater indicators and heat requests do
not measure electrical power or energy. This independent community project is
not affiliated with or endorsed by Meier Tobler AG.

## Subsequent technical installation evidence

A separate read-only installation report on 2026-11-01 confirmed version 0.6.0
and byte-identical contents for all 19 integration files, with the existing
flow-target entity and valid HA configuration. This establishes installed source,
not independent HACS-path or rendered-UI acceptance. The later dashboard-only
check does not prove another integration upgrade or a physical write test.
