# Field smoke test: 0.3.0

Status: **PASS**
Test date: 2026-09-20
Release candidate: `v0.3.0`
Commit: `94b7305c3fcb61b3647452637fb479735a66e8b7`
Bundle SHA-256: `190b3aeb71e43fed8592242416ed5cd702bdbc9c2e82bdb279b4cea4d9209dc5`

## Scope and results

- The deterministic bundle produced by the successful Release Gate was used.
- The installed integration was upgraded from 0.2.0 to 0.3.0 after a successful Home Assistant configuration check and backup.
- Home Assistant restarted successfully and reported integration version 0.3.0.
- All eight sensors and the writable HK60 mode select were available after startup and after a UI reload.
- Sensor values and the selected mode were plausible and consistent with the existing installation.
- Downloaded diagnostics redacted the configured host, device serial number, and global device identifier. No credentials were present.
- A UI write/readback test changed the requested mode from Auto to Cooling and then back to Auto. Both writes were reflected by the select and the read-only mode sensor.
- After restoring Auto, the controller returned from cooling/cooling season to heating/heating season without intervention.
- Existing Home Assistant YAML configuration and automations were not modified by the installer.

No host names, local addresses, credentials, device serial numbers, global device identifiers, or Home Assistant entry identifiers are recorded in this report.

## Release decision

The field smoke test passed. Publishing the repository and creating a GitHub Release remain separate, explicit decisions. This report does not publish a release and does not change the tested `v0.3.0` tag or bundle.
