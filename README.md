# Meier Tobler SmartGuard for Home Assistant

A local Home Assistant integration for Meier Tobler SmartGuard 2.0 gateways.

## Status

Version [`0.3.0`](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/tag/v0.3.0)
is the first public, field-tested release. It provides:

- UI configuration and connection validation;
- stable device identification from the gateway API;
- one coordinated update every 60 seconds;
- eight sensor entities for the currently verified controller and HK60 data;
- one HK60 operating-mode select with an allowlist and immediate readback;
- redacted diagnostics for support and local troubleshooting;
- one tested, guarded night-heating blueprint with a stable public source;
- reconfiguration when the gateway address changes;
- no external Python runtime dependency.

The select writes only the six verified operating modes. A successful HTTP
response is not trusted on its own: the integration immediately reads the
datapoint back and reports an error unless the gateway confirms the requested
value. The displayed state is never changed optimistically.

## Important security limitation

The locally verified SmartGuard REST data API is available over HTTP without
authentication. The password configured in the local SmartGuard user interface
does not protect this HTTP REST endpoint. Version `0.3.0` therefore communicates
only over local HTTP and never stores SmartGuard credentials.

Use this integration only on a segmented local network. Restrict TCP port 80 on
the gateway to the Home Assistant host, block access from unrelated networks,
and never publish the gateway API to the internet.

## Installation

### HACS custom repository

Until this project is included in the default HACS catalogue, add it as a
custom integration repository:

1. Open **HACS** in Home Assistant.
2. Open the three-dot menu and select **Custom repositories**.
3. Enter `https://github.com/martins-netizen/ha-meiertobler-smartguard`.
4. Select **Integration** as the category and add the repository.
5. Open **Meier Tobler SmartGuard**, select **Download**, choose version
   `v0.3.0`, and restart Home Assistant when HACS requests it.
6. Open **Settings > Devices & services > Add integration** and select
   **Meier Tobler SmartGuard**.

Adding a custom repository only registers its metadata in HACS. Integration
files are changed only after **Download** or **Redownload** is selected. The
first end-to-end HACS installation test is tracked separately in the
[HACS 0.3.0 test record](docs/HACS_TEST_V0.3.0.md).

### Manual installation

Download the attached `meiertobler_smartguard-0.3.0.zip` from the
[0.3.0 release](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/tag/v0.3.0),
verify its published SHA-256 checksum, and extract it into the Home Assistant
configuration directory so that the integration is located at
`/config/custom_components/meiertobler_smartguard`. Restart Home Assistant,
then open:

1. Settings
2. Devices & services
3. Add integration
4. Meier Tobler SmartGuard

Enter only the hostname or IP address. Do not enter `http://`, a path, a port,
or credentials.

During a controlled migration, keep the existing YAML/REST configuration
active until its automations and dashboards have been migrated. Both select
entities control the same physical datapoint, so do not operate them
concurrently.

## Sensors

| Sensor | API datapoint |
| --- | --- |
| Source inlet temperature | `101001` |
| Condenser inlet temperature | `101008` |
| Condenser outlet temperature | `101009` |
| HK60 flow temperature | `1001` |
| HK60 operating status | `5003` |
| HK60 selected operating mode | `5004` |
| HK60 effective operating mode | `5005` |
| HK60 season status | `5009` |

## HK60 operating-mode select

The select exposes the verified options `auto`, `normal`, `reduced`,
`frost_protection`, `heating`, and `cooling`. Home Assistant translates these
stable internal values for display. Every changed option is written to datapoint
`5004`, read back immediately, and followed by a coordinated refresh.

## Compatibility

- Home Assistant `2026.9.0` or newer
- Meier Tobler SmartGuard 2.0 with device type `1001`
- HK60 enabled for the five HK60 entities

This is an independent community project and is not affiliated with or endorsed
by Meier Tobler AG.

## Diagnostics

Home Assistant can download diagnostics for each SmartGuard config entry. The
diagnostic data includes the current coordinator status and the latest values
already held in memory; it does not trigger additional gateway requests. The
configured host, global device identifier, and serial number are always
redacted. The integration does not store or expose a SmartGuard password.

## Documentation

- [Troubleshooting](docs/TROUBLESHOOTING.md) describes recognizable symptoms,
  their causes, and safe resolution steps.
- [Automation examples](docs/AUTOMATION_EXAMPLES.md) provides guarded examples
  and a prepared blueprint that do not silently overwrite a manual
  operating-mode choice.
- [HACS 0.3.0 test record](docs/HACS_TEST_V0.3.0.md) documents the controlled
  custom-repository installation procedure and its current result.
- [Release and publication checklist](docs/RELEASE_CHECKLIST.md) separates the
  read-only release gate from an explicit publication decision.
- [Changelog](CHANGELOG.md) records the development history, and the
  [0.3.0 release notes](docs/RELEASE_NOTES_0.3.0.md) describe the published
  release and its validation evidence.

Bug reports use a structured issue form and must contain only sanitized,
synthetic installation data. Security vulnerabilities must be reported
privately as described in [SECURITY.md](SECURITY.md).

## Development and HACS status

The repository is public, and the Quality, Hassfest, and official HACS
validation jobs pass on the protected `main` branch. Version `0.3.0` is a full
GitHub release and can be selected after adding this project to HACS as a custom
integration repository. Inclusion in the default HACS catalogue has not been
requested.

The current `hacs.json` uses HACS' standard integration layout. HACS therefore
installs `custom_components/meiertobler_smartguard` from the selected tagged
repository source. The separately attached deterministic ZIP is the verified
manual-installation bundle; it is not declared as a HACS `zip_release` asset.

## Release gate

The repository contains a read-only release workflow. An annotated tag in the
stable form `vMAJOR.MINOR.PATCH` must match both
`manifest.json` and `pyproject.toml`, and its commit must belong to `main`.
The workflow then repeats repository validation, Ruff, strict MyPy, and the
complete test suite before building a deterministic integration ZIP and a
SHA-256 checksum.

The workflow uploads these files only as a temporary GitHub Actions artifact.
It does not create or publish a GitHub release. After manual inspection, a
release must still be created explicitly; therefore pushing a tag alone can
never publish this integration. Version `0.3.0` completed this process before
its public release.

## Removal

Before removing the integration, remove its config entry in Home Assistant under
Settings > Devices & services. If it was installed manually, remove
`custom_components/meiertobler_smartguard` and restart Home Assistant. If it was
installed through HACS after public release, use the HACS removal action and
restart Home Assistant.

During the controlled migration period, do not remove the existing YAML/REST
configuration until its automations and dashboard references have been migrated
and verified separately.

## Development checks

Run the deterministic repository checks with:

```bash
python3 scripts/validate.py
python3 scripts/release.py check
python3 scripts/release.py verify-tag --tag v0.3.0
python3 scripts/release.py build --output-directory dist
python3 -m ruff check .
python3 -m mypy \
  custom_components/meiertobler_smartguard \
  scripts/release.py \
  tests/test_release.py
python3 -m pytest -q \
  --cov=custom_components/meiertobler_smartguard \
  --cov-report=term-missing \
  --cov-fail-under=95
```

The test suite covers the API and write-verification layer as well as the
config flow, coordinator, entity formatting, select error handling, redacted
diagnostics, setup, unload, and reload behavior. CI enforces at least 95 percent
statement and branch coverage, validates documentation and repository security
invariants, and runs strict MyPy checks for the full integration. Recovery
behavior will be covered together with that feature in a later development
release.
