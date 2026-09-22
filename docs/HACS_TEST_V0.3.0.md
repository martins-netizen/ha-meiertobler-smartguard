# HACS custom-repository test: 0.3.0

Status: **PASS**
Test date: 2026-09-21 (Europe/Zurich)

## Purpose

This post-release test verifies that HACS discovers public release `v0.3.0`,
installs the expected integration files, requests a Home Assistant restart, and
leaves the existing SmartGuard config entry and entities operational.

The repository does not declare `zip_release` in `hacs.json`. HACS therefore
installs the tagged `custom_components/meiertobler_smartguard` source tree. The
attached `meiertobler_smartguard-0.3.0.zip` is a separately verified
manual-installation bundle and must not be described as the file selected by
HACS. Both integration trees originate from the same annotated tag and are
expected to contain identical integration files.

## Preconditions

- The public GitHub release `v0.3.0` remains marked as Latest.
- Tag `v0.3.0` still resolves to
  `94b7305c3fcb61b3647452637fb479735a66e8b7`.
- The existing Home Assistant installation reports integration version `0.3.0`.
- A Home Assistant configuration check and an external backup complete before
  HACS writes any files.
- The current mode is recorded but not changed for this distribution test.

## Controlled procedure

1. Run the read-only/preparation phase of the repository test script. It must
   verify the public release, compare the current integration with the tagged
   source, run a Home Assistant configuration check, and create backups.
2. In HACS, open the three-dot menu and select **Custom repositories**.
3. Add `https://github.com/martins-netizen/ha-meiertobler-smartguard` with type
   **Integration**.
4. Confirm that HACS shows `v0.3.0` before selecting **Download**. Adding the
   repository alone must not change the integration files.
5. Download version `v0.3.0` and restart Home Assistant only when HACS requests
   it.
6. Run the verification phase of the test script.
7. Confirm in Home Assistant that all eight sensors and the HK60 mode select are
   available, the selected mode is plausible, reload succeeds, and diagnostics
   remain redacted.

The mode select is not exercised during this HACS distribution test. Its
write/readback behavior already passed the field smoke test, and changing a
physical controller mode is not required to verify package distribution.

## Pass criteria

- HACS resolves and downloads `v0.3.0` without validation or structure errors.
- The installed integration tree matches the tagged source byte for byte.
- Home Assistant passes its configuration check and restarts successfully.
- The existing config entry loads without reconfiguration or credential input.
- Eight sensors and one select remain available after restart and UI reload.
- No YAML configuration, automation, dashboard, or SmartGuard operating mode is
  changed by the test.

## Result and evidence

- The repository owner confirmed that HACS accepted the custom integration
  repository, offered v0.3.0, completed the download/redownload, and that
  Home Assistant restarted successfully when requested.
- Before the HACS operation, the preparation script verified the public
  release, annotated tag, release ZIP checksum, and the installed 0.3.0
  integration tree; it completed a Home Assistant configuration check and
  created local and Home Assistant backups.
- After the HACS operation, the verification script confirmed registration
  without printing HACS storage content. The installed integration tree
  matched the annotated tag, release ZIP contents, and pre-install baseline
  byte for byte. Its tree digest was
  `4431d1ae059d1cd7c96c738c16a536479c3b9a6496045f03cb931d9b693c3ac6`.
  The Home Assistant configuration check succeeded again.
- The repository owner confirmed that SmartGuard 2.0 showed eight available
  sensors and one mode select after restart. The select showed Auto, and a
  manual integration reload returned all nine entities within 60 seconds.
- The owner checked the downloaded diagnostics and confirmed
  `config_entry.data.host`, `identity.serial_number`, and
  `identity.global_device_id` were each `**REDACTED**`.
- The public main Validate run for commit
  `718d992e0ec4ea89f7e1177a65dad186031f4f91` succeeded:
  https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/runs/35648501547

The preparation script's final summary displayed `HACS-Version: 0.3.0`;
this label referred to the SmartGuard integration version. The actual HACS
version recorded before the test was 2.0.5.

The user-interface results above were reported by the repository owner. This
record contains no raw diagnostics, host address, device serial number, global
device identifier, or Home Assistant config-entry identifier.

## Recovery

If downloading or restarting fails, stop the test, preserve the HACS and Home
Assistant logs, and restore the integration directory from the preparation
backup. Do not move the release tag or silently replace a published asset.

This record documents the completed post-release HACS distribution test.
