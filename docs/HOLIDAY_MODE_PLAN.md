# Scheduled holidays, heating and presence simulation

Status: **two read-only timestamp sensors implemented in the unreleased scope**.
Scheduling, holiday writes and presence-simulation coupling remain **design only**.
Published 0.6.0 does not include these timestamp sensors. No new gateway action
or presence automation is provided by this change.

## Current read-only stage

The existing enabled HK60 module contributes two optional diagnostic sensors:

| Reading | Datapoint | Value exposed to Home Assistant |
| --- | --- | --- |
| Holiday start · HK60 | `1/2/5226` | Timezone-aware UTC timestamp |
| Holiday end · HK60 | `1/2/5227` | Timezone-aware UTC timestamp |

The supplied frontend converts local date/time input with
`Math.floor(new Date(value).getTime() / 1000)` and reconstructs dates from
`1000 * value`. Independent read-only replies confirmed integer values at both
points. The wire format is therefore whole Unix seconds. Keep the integration's
verified gateway identity and circuit path, rather than copying a hardcoded
device identifier from the frontend.

HA displays the reported instants in its configured timezone. The integration
does not add a fixed UTC offset or mutate local time components. Synthetic
winter, summer, rollover and both repeated autumn-hour cases are tested. The
frontend's local-minute adjustment can cross a DST boundary; it is not used as
a conversion algorithm here.

Only positive integers representable through `9999-12-31T23:59:59Z` are accepted.
These are serialization guards, **not verified firmware scheduling limits**.
Zero has not been confirmed as an unset/disabled marker and is unavailable,
rather than displayed as a real holiday in 1970 or treated as a successful clear.
Booleans, numeric strings, floats and out-of-range values are also unavailable.
An invalid optional point does not fail core polling or the other date, and a
later valid reply recovers the same entity. Existing IDs/custom names survive reload.

No unit or statistics state class is attached. Each enabled HK60 refresh adds
exactly two GETs and reuses its existing config check; disabled modules are not
queried for these points. The complete unreleased scope uses up to 44 GETs and
45 entities (32 numeric/enum/timestamp, six label, six binary, one select).
Disabling an entity in the registry alone does not stop its coordinated read.

Both exact dates are redacted in downloaded integration diagnostics. They are
still available as entity states for the owner's intended HA use; normal HA
state access/history protections apply. Reading them does not modify a period,
validate that start precedes end, or prove that firmware holiday operation is
active. No derived active flag, date-setting action or `5241` entity is added.

## A period can be planned independently

A user must be able to choose a holiday start and end at any time, including
before departure and without a preceding 24-hour absence. One confirmed period
is intended to coordinate both SmartGuard holiday operation and the existing
lighting presence simulation. Selecting start/end alone must not perform a
physical write before the final explicit confirmation.

The confirmation must show the verified circuit, previous/new period, known
heating effect and the lighting-simulation behavior. The user can inspect,
change or cancel the period. Every future manual change needs a new explicit
confirmation, tied to the concrete period and verified target.

At the confirmed start, enable presence simulation according to its existing
daily lighting schedule. Do not turn on all lights at midday or reinterpret a
daytime pause as the end of the holiday. Preserve the independent lighting
automation, manual-light choices and the existing keep-lights option.

At the planned end, withdraw only actions/settings owned by this period. A
manually active simulation or a subsequently changed heating plan must not be
silently cancelled. An earlier return should offer early termination for
confirmation. The normal end already forms part of the previously confirmed
period; gateway activation/restoration semantics still need verification.

## Long absence is an additional suggestion

Track continuous, reliably known absence of all selected people separately
from the light simulation. After a configurable threshold (initial proposal:
24 hours), HA may suggest creating a holiday period if there is no applicable
confirmed plan. This does not restrict manual planning to people already away.

A lighting simulation is a consumer of the holiday/absence decision, not its
source: its sunset schedule, daytime pause or manual light switch must not
count as a return. Unavailable presence data is not proof of absence.
Persist the absence start across HA restarts, check elapsed UTC time at startup
and use the installation timezone only for display and verified gateway encoding.
Handle DST, late confirmation and someone returning before confirmation.

Ask for an intended end time; never invent an unlimited or repeatedly extended
period. Do not overwrite an existing manual SmartGuard schedule. Suggestions
and early-return messages do not themselves authorize physical changes.

## Verify the gateway contract first

The supplied frontend references start `5226`, end `5227` and holiday field
`5241`. Its circuit block is a template; use the installation's verified active
circuit. Field `5241` has unit K in the HTML and must not be assumed to be a
boolean holiday-active flag.

The supplied frontend confirms a separate POST for each date, with a numeric
JSON `value` in a `text/plain` body. It checks HTTP success only. It does not
atomically update a period or immediately read both values back. The supplied
date handler also has no joint-period validation or explicit confirmation.
That demonstrates the UI request format, not a successful physical write test.

Unset/disabled values, activation rules, inclusive/exclusive boundaries,
supported date range, write ordering and partial-write behavior still need
verification. Field `5241` is a display cell in the supplied HTML; its K value
does not reveal the regulated target or its effect. No real planned absence
dates, personal identities or raw device data should be published as evidence.

Immediately before a future confirmed write, recheck target identity and the
unchanged source schedule. Keep per-period ownership for only the state created
by this operation. If heating and lighting cannot both be prepared, report the
partial state accurately; do not claim complete activation or blindly revert a
later manual change. Direct unconfirmed actions must not bypass the guided
request. The existing authorized night-mode recovery stays intact.

Integration holiday support and the user-specific presence-simulation binding
are separate implementation steps. Do not silently alter room targets,
frost-protection, hot-water schedules or legionella settings as part of this plan.
Synthetic tests and an exact, explicitly confirmed period with a clear return
path are required before a physical write test. This document is not a live
installation acceptance report.
