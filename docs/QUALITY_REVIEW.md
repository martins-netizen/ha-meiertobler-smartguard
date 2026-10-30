# Blueprint and quality evidence review

Reviewed against the published 0.4.1 source and the repository's current
integration/blueprint implementation. The rule statuses below are maintained
in [quality_scale.yaml](../custom_components/meiertobler_smartguard/quality_scale.yaml).

## Blueprint findings and correction

The earlier blueprint returned any selected `heating` mode to `auto` in the
morning, even when it had not selected heating itself. Its two tests validated
schema and input substitution, not actual actions. The documentation's claim
that a manual selection was never overwritten was therefore too broad.

The corrected [blueprint](../blueprints/automation/martins_netizen/smartguard_guarded_night_heating.yaml)
requires a separate persistent ownership toggle. It sets that marker only after
a successful service call with `heating` reported, requires it for morning
recovery, and clears it after a known different mode. Time and state events are
serialized. Unavailable states do not erase the marker. Night temperature must
be a finite number in °C, and the enable and ownership helpers must differ.

See [setup, re-import and limitations](AUTOMATION_EXAMPLES.md) before using it.
In particular, selecting Heating again while already Heating cannot identify
a new manual intention, and no startup/reconnection catch-up is provided.

## Evidence and remaining work

| Item | Evidence | Remaining work |
| --- | --- | --- |
| Blueprint schema and inputs | Home Assistant schema/substitution tests, including the newly required helper | Select both distinct helpers in the UI |
| GitHub import | HA importer consumes mocked HTTP content at the documented public URL; validates the owner-derived stored path and substituted automation | New user's real UI preview/import/save remains unconfirmed |
| Night/morning behavior | Actual HA time/state triggers, real input booleans and simulated select service | Production replacement remains a separate decision |
| Manual choice | No morning write without ownership; changing away and immediately back clears ownership | Identical-value or unobserved manual writes cannot be distinguished |
| Restart and failures | Restored helper, unavailable select, failed/unconfirmed writes and missing/non-finite temperature tests | No claim of a new physical gateway cycle |
| Existing installation | Maintainer has previously verified its own night automation and HACS 0.4.1 with all 15 entities | That is not a field test of this changed public blueprint |

The automated tests are in [test_blueprint.py](../tests/test_blueprint.py).
They neither contact a gateway nor alter the maintainer's Home Assistant.

Local validation used Python 3.14.8 and the hash-pinned CI environment with
Home Assistant 2026.9.3: **155 tests and 26 subtests passed**, including 30
blueprint cases; integration statement/branch coverage remains **100%**.
The manual-heating regression test fails against the original blueprint and
passes against the corrected one. Repository validation, Ruff and dependency
consistency passed. Strict MyPy passed for its 13 configured source files using
a process-local workaround for this host's unavailable psutil PID lookup; the
repository dependencies and CI MyPy command were not changed.

## Quality checklist corrections

| Rule | Current status and reason |
| --- | --- |
| `reauthentication-flow` | Exempt: the verified local HTTP API does not authenticate integration requests; remove the obsolete 0.3.0 qualifier |
| `docs-examples` | Todo: automated import/execution evidence is now present; keep the previously required UI/import and production migration confirmation open |
| `entity-disabled-by-default` | Todo: optional diagnostic operating-hour counters are enabled by default; the old exemption for only the original functional core is no longer accurate |
| `discovery` | Todo: no reliable local discovery mechanism verified |
| `repair-issues` | Done on development main: entry-specific notices for invalid saved hosts, unsupported devices and changed gateway identities; transient/ambiguous failures retain retries |

This review does not disable existing entities, change integration defaults,
add discovery, or change a release/tag. Other existing checklist entries
are retained; this is a focused blueprint/evidence review, not a new audit of
every rule. Future default changes need a separate behavior/migration review.

## Actionable configuration repairs on development main

Existing entries stop setup and receive a translated repair when the saved
host is invalid, the responding device is unsupported, or its global identity
differs from the saved identity. A mismatched gateway is rejected before
reading measurements or exposing controls. The original identity is retained;
legacy entries without a saved unique ID are not falsely labelled mismatched.

Notices are persistent, scoped by config-entry ID, deduplicated, and replaced
when a different permanent cause is confirmed. A successful identity check
clears them; an ambiguous timeout does not prove recovery. Entry removal clears
only that entry's notices. The descriptions link to the existing reconfigure
UI and explain how to reload a restored original gateway. There is no automatic
repair action or gateway write. Temporary communication/measurement failures
keep normal retries without new repair notices.

[Native HA lifecycle tests](../tests/test_issues.py) cover blocked setup,
transient failures, reconfiguration, unchanged entity IDs, multiple entries,
removal and privacy. Both existing EN/DE catalogs contain issue and setup-error
translations. This is automated evidence; no rendered repair UI, live gateway
fault or productive installation is claimed. The published 0.4.1 release does
not yet contain these development changes.

## Reference contracts

- [HA blueprint import and re-import](https://www.home-assistant.io/docs/automation/using_blueprints/)
- [HA disabled-by-default rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/entity-disabled-by-default/)
- [HA actionable repair issues](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues/)

Re-import can change all automations that use that blueprint. The new ownership
input must be supplied explicitly; updating the HACS integration alone does not
update an imported blueprint. Existing production automations are not migrated
by this repository change.
