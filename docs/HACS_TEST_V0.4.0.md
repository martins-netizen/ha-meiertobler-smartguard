# HACS 0.4.0 upgrade result

Status: **PASS** for the user-reported update and entity-availability check.
Reported on 2026-10-23.

The maintainer confirmed that the existing HACS installation updated to the
published 0.4.0 release successfully and that all existing entities were present.
The established installation has 15 entities with both storage modules enabled.

This is a user-confirmed UI outcome. No new independent filesystem, registry,
configuration, diagnostic-redaction or physical operating-mode test was performed
for this report. A restart was requested in the test instructions but was not
separately reported; no distinct restart/reload timing claim is made here.
The earlier byte-verified feature installation and 0.3.0 installation test remain
separate historical evidence.

HACS uses the tagged integration source tree. Release tag `v0.4.0` and its two
assets were independently verified during publication; the release ZIP is the
manual-installation bundle, not a HACS `zip_release` asset.

No private readings, hostnames, device identifiers or diagnostics are published.
