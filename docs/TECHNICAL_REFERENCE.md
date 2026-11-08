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

See [additional operating readings](OPERATING_READINGS.md) for the 0.5.0
room targets, outdoor temperature, Smart Grid status, fault inputs and buffer
heat request, including their separate availability and read-only semantics.

The **0.6.0** [HK60 flow target and limits](HK60_FLOW_AND_LIMITS.md) add the
current flow target and nine controller parameters as optional sensors.
Configured circuit/storage labels provide readable display names and diagnostic
metadata while existing entity IDs and personal names remain intact.

The **0.7.0 release** adds four read-only heating-curve diagnostics and two
holiday timestamps, with shorter HK60 measurement names. All optional readings
available: **45 entities and 44 GETs** per complete refresh. See
[release notes](RELEASE_NOTES_0.7.0.md) for publication status and scope.

The latest stable release is [0.7.1](RELEASE_NOTES_0.7.1.md), which fixes holiday
date prefilling without changing this entity set or polling. On `main`, the
two heater operating-hour counters default to disabled for new registry
entries; this is [unreleased](../CHANGELOG.md#unreleased). Existing registry
choices are retained, and disabling an entity does not stop its coordinated read.

## HK60 writes

The allowlisted options are `auto`, `normal`, `reduced`, `frost_protection`,
`heating` and `cooling`. Home Assistant translates these stable internal values
for display. Each changed option is written to datapoint `5004`, read back
immediately and followed by a coordinated refresh. A successful HTTP response
alone does not confirm a write, and state is not changed optimistically.

The release also offers a guided [whole-period holiday editor](HOLIDAY_MODE_PLAN.md).
It writes only observed start/end points after explicit confirmation and fresh
source checks, then reads the complete period back. There is no atomic gateway
transaction; the exact intermediate period is shown before confirmation.
Physical holiday behavior remains unverified. No generic write service or
editable temperature entity bypasses the flow. Gateway requests refuse redirects.

## Diagnostics

Downloaded diagnostics use the coordinator's existing in-memory values; they
trigger no additional gateway request. Host, global device ID and serial number
are redacted, together with free-text module labels and exact holiday times.
The integration stores no SmartGuard credentials and has no
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

Use Python 3.14.10 or a later 3.14 patch and the pinned, hash-checked CI dependencies
described in [CONTRIBUTING.md](../CONTRIBUTING.md#ci-dependency-updates).

| Environment | Home Assistant | Requirements | Pytest plugin |
| --- | --- | --- | --- |
| Current HA | 2026.11.0 | `.github/requirements-ci.txt` | `pytest-homeassistant` |
| Minimum HA | 2026.9.0 | `.github/requirements-ci-minimum.txt` | `pytest-homeassistant-custom-component` |

Install each dependency set in its own virtual environment, using the pinned
build tools and hash-checked install flags from the contribution guide. Do not
install both plugins together or update the minimum baseline as part of a
routine current-environment dependency update. Run `python3 -m pip check`,
repository validation and the complete test suite in each environment.
The protected Quality check requires both environments; Ruff and strict MyPy
run in the current environment. From the repository root:

```bash
python3 scripts/validate.py
python3 scripts/release.py check
python3 scripts/release.py verify-tag --tag v0.7.1
python3 scripts/release.py build --output-directory dist
python3 -m ruff check .
python3 -m mypy \
  custom_components/meiertobler_smartguard \
  scripts/release.py \
  tests/test_release.py
python3 -m pytest -q \
  --disable-socket --allow-hosts=127.0.0.1,::1 \
  --cov=custom_components/meiertobler_smartguard \
  --cov-report=term-missing \
  --cov-fail-under=95
```

Run the complete suite for release-status changes, including release-note tests.
The `verify-tag` command above checks the tag name against the working-tree
version only. The tagged Release Gate separately verifies the annotated tag,
exact commit and `main` ancestry. Building the development tree with unchanged
version metadata does not reproduce or publish the existing 0.7.1 release;
use its [published integrity record](RELEASE_NOTES_0.7.1.md) for that download.
Synthetic candidate cases use fixed text independently of the current release
notes. CI requires at least 95 percent statement and branch coverage. The suite
covers setup, unload/reload, config flow, coordinator, API/write verification,
entity formatting, optional readings and redacted diagnostics. Blueprint tests
also exercise the HA GitHub importer with mocked HTTP, time/state triggers,
helper restoration and simulated mode writes. Real UI import and production
replacement remain separate, unclaimed checks. See the
[blueprint and quality evidence review](QUALITY_REVIEW.md).
