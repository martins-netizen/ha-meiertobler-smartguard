# Additional storage measurements

Status: **PASS** for read-only gateway verification and Home Assistant feature
installation testing. Included in the published
[0.4.0 release](RELEASE_NOTES_0.4.0.md). The subsequent HACS
upgrade and entity availability were user-confirmed; see
[the upgrade record](HACS_TEST_V0.4.0.md).

## Data sources

The manufacturer's [SmartGuard network and data access documentation](https://dokumente.meiertobler.ch/files/product-assets/90355/lvxlo.pdf)
defines the module configuration format on page 9 and the values on pages
18-19. Paths below are relative to `/api/v1/1001/<serial_number>`.

| Measurement | Module | Datapoint | Type / unit |
| --- | --- | --- | --- |
| Heating buffer temperature B30 | `2/1` | `1001` | Decimal, °C |
| Heating buffer heater indicator | `2/1` | `3191` | Boolean |
| Heating buffer heater operating hours | `2/1` | `3192` | Integer, h |
| Hot water temperature B40 | `3/1` | `1001` | Decimal, °C |
| Hot water heater indicator | `3/1` | `4191` | Boolean |
| Hot water heater operating hours | `3/1` | `4192` | Integer, h |

## Availability and interpretation

Each update reads the module's `/config` endpoint. Only `enabled: true` enables
its additional GET requests. Entities are registered after the first valid
reading, including when a module becomes available after startup.

A missing, malformed or temporarily inaccessible optional reading makes its
existing entity unavailable. Other readings continue to update. Temperatures
outside the documented -50 to 125 °C range, including the -273.15 °C sentinel,
are rejected. A boolean false and an operating-hour count of zero remain valid.

The heater indicators are the statuses reported by SmartGuard. They do not
measure the physical ASKOHEAT devices' electrical power or energy consumption.
This extension adds no heater controls or setpoint changes.

## Default activation in the next release

The development source makes the two diagnostic heater operating-hour counters
disabled by default when first registered. They remain available under
**Settings → Devices & services → Entities**: include disabled entities in the
filter, open the counter and enable it when needed. Temperatures and heater
indicators keep their existing defaults.

This default applies only to newly created entity-registry entries. Existing
enabled counters stay enabled; disabled counters, custom entity IDs and names
retain their saved choices, including after an integration reload. No registry
migration is performed. The reading of SmartGuard datapoints is unchanged.
Published 0.7.1 retains its original defaults; this adjustment is for a future
release.

## Verification before release

- [x] Check API paths and types against the manufacturer documentation.
- [x] Verify module configuration and the six read-only endpoints on a live gateway.
- [x] Cross-check the two storage temperature readings against a device display.
- [x] Confirm entity discovery, units and availability on the test installation.
- [x] Confirm preservation of existing entity IDs and personal settings.

## Read-only verification outcome

The six optional endpoints returned values of the documented types, and a
display comparison supported the two temperature mappings. The detailed
measurement report and installation-specific sensor labels remain private.
No write, reload or restart was performed by the read-only probe.

## Home Assistant installation outcome

The merged feature source was installed and verified byte for byte. All 15
entities were available: the original eight sensors and HK60 select, plus two
storage temperatures, two diagnostic operating-hour counters and two heater
indicators. Temperature and inactive-indicator display was confirmed; zero
operating hours remained valid. Existing IDs, personal settings and protected
Home Assistant configuration were preserved. The installer made no mode writes.

This feature installation test preceded publication. The subsequent tagged
bundle and publication checks are recorded in the [0.4.0 release notes](RELEASE_NOTES_0.4.0.md).
The subsequent HACS upgrade and entity availability were user-confirmed in the
[upgrade record](HACS_TEST_V0.4.0.md); no new independent byte or restart check
is claimed. Raw diagnostics, measurements,
hostnames and device identifiers remain private.
