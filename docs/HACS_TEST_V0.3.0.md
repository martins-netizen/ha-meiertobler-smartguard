# HACS custom-repository test: 0.3.0

Status: **PENDING**

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

## Recovery

If downloading or restarting fails, stop the test, preserve the HACS and Home
Assistant logs, and restore the integration directory from the preparation
backup. Do not move the release tag or silently replace a published asset.

After all pass criteria are confirmed, update this record to **PASS** in a new
pull request with the test date and privacy-safe evidence.
