# Technical reference and development

[Back to the overview](../README.md)

## Core readings

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

See [additional measurements](ADDITIONAL_MEASUREMENTS.md) for optional modules,
paths, types, units and availability behavior.

## HK60 writes

The allowlisted options are `auto`, `normal`, `reduced`, `frost_protection`,
`heating` and `cooling`. Home Assistant translates these stable internal values
for display. Each changed option is written to datapoint `5004`, read back
immediately and followed by a coordinated refresh. A successful HTTP response
alone does not confirm a write, and state is not changed optimistically.

## Diagnostics

Downloaded diagnostics use the coordinator's existing in-memory values; they
trigger no additional gateway request. Host, global device ID and serial number
are redacted. The integration stores no SmartGuard credentials and has no
external Python runtime dependency. The local HTTP REST endpoint has no
authentication, even when the gateway UI has a password.

## Release and HACS layout

HACS installs the integration from the selected tagged source tree. The
separately attached deterministic ZIP is for manual installation. The annotated
tag must match the manifest, project and lock-file root version and belong to
`main`. The read-only Release Gate validates and builds but never publishes.
Tags and assets are not moved or silently replaced after publication.

Keep the README useful across the tag/publication boundary: link to Releases
for availability instead of embedding temporary candidate/publication claims.
Candidate status belongs in versioned release notes and the release checklist.
The image in the README is an illustrative overview using the existing community
icon, not a screenshot or a manufacturer product image. Its SVG source and PNG
export are in `docs/images`; absolute public image URLs work in the HACS view.

## Development checks

Use Python 3.14 and the pinned, hash-checked CI dependencies described in
[CONTRIBUTING.md](../CONTRIBUTING.md). Run from the repository root:

```bash
python3 scripts/validate.py
python3 scripts/release.py check
python3 scripts/release.py verify-tag --tag v0.4.1
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

Run the complete suite for release-status changes, including release-note tests.
Synthetic candidate cases use fixed text independently of the current release
notes. CI requires at least 95 percent statement and branch coverage. The suite
covers setup, unload/reload, config flow, coordinator, API/write verification,
entity formatting, optional readings and redacted diagnostics. Blueprint tests
also exercise the HA GitHub importer with mocked HTTP, time/state triggers,
helper restoration and simulated mode writes. Real UI import and production
replacement remain separate, unclaimed checks. See the
[blueprint and quality evidence review](QUALITY_REVIEW.md).
