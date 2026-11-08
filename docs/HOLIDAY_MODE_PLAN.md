# HK60 holiday editor and separate presence-simulation plan

Status: **two read-only timestamp sensors and a confirmed whole-period editor
published in 0.7.0**, with date-prefilling fixed since **0.7.1**. See the [release notes](RELEASE_NOTES_0.7.1.md).
Successful date readback confirms stored values; physical holiday operation
and heating effect remain separate live acceptance.

This repository supplies the SmartGuard sensors and confirmed editor. The
orchestration proposal below does not add lighting presence simulation, absence
tracking, a calendar, a dashboard or adaptive preheating to the integration.
Installation-specific Home Assistant configuration is separate and is not a
published SmartGuard feature or a gateway-acceptance record.

## Read-only holiday sensors

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
queried for these points. The complete 0.7.0 release uses up to 44 GETs and
45 entities (32 numeric/enum/timestamp, six label, six binary, one select).
Disabling an entity in the registry alone does not stop its coordinated read.

Both exact dates are redacted in downloaded integration diagnostics. They are
still available as entity states for the owner's intended HA use; normal HA
state access/history protections apply. Reading them does not modify a period,
validate that start precedes end, or prove that firmware holiday operation is
active. No derived active flag or `5241` entity is added. Date editing uses the guided
options dialog below; the two timestamp entities remain read-only.

## Confirmed whole-period editor

Open **Settings > Devices & services > Meier Tobler SmartGuard > Configure**.
The integration must be loaded. Select both dates in the displayed HA timezone,
review the old/new complete periods, circuit label and selected mode, then
explicitly confirm. Cancelling or leaving the checkbox clear cannot write.
The confirmation expires after five minutes and is consumed before network I/O.
No generic write service or independently writable date entity bypasses it.
Dates are held only in flow memory, not copied into config-entry options.

Before writing, the client rechecks the physical gateway identity, enabled HK60
module, mode, label and unchanged source pair. It reads the pair twice to detect
observed changes while reading. All local writes share the existing mode-write
lock. Confirmation expiry and the future end are rechecked inside that lock
after the source read. API requests do not follow redirects to another target. These are best-effort conflict checks: the gateway offers no compare-and-set
or transaction, so an external writer can still race between requests.

The order preserves start < end at each intermediate step: start first when it
is before the existing end, otherwise end first. Unchanged endpoints are skipped.
The confirmation shows the exact first intermediate period and write count.
Moving an old period into the future can temporarily extend the old end, which
may activate holiday operation immediately. This is explicitly warned about;
atomicity or harmless intermediate operation is not claimed.

Both dates and context are read back after every successful POST. A rejection,
timeout, differing readback or changed context stops subsequent writes. One
read-only recovery attempt reports the actual pair, or an unknown result. A
lost reply is accepted only if the entire requested state is independently
confirmed. No automatic retry or blind rollback can overwrite a later manual
change. After interruption, check SmartGuard and open a fresh confirmed request.

Whole positive Unix seconds, ordered dates and an end still in the future are
required. Earlier starts are permitted for already-started absences. Local times
in the spring gap or repeated autumn hour are rejected without an explicit
offset; do not guess. Conversion uses HA's timezone and UTC instants, without
the frontend's local-minute adjustment. Unknown zero/unset values are rejected;
no clear/disable behavior is invented. Maximum representable timestamp is a
serialization bound, not a proven firmware scheduling limit.

The editor changes only 5226/5227 on verified 1/2, using the supplied frontend's
numeric JSON value with text/plain POST. It does not change the selected mode,
holiday reduction, room targets, heating curve, hot water or lighting simulation.
Successful readback proves stored dates only. It does not prove holiday-active
status, the reference of the displayed K reduction or correct heating behavior.
The first physical test needs a separately chosen and confirmed concrete period
with previous values retained and a reviewed return path.

## Separate Home Assistant orchestration proposal

The following sections describe a separate design, not behavior implemented by
this integration. The reported SmartGuard end is the controller's stored holiday
end; it is not necessarily a person's actual return time. Any external logic
that brings heating forward must keep those two times distinct and retain its
own confirmed plan and ownership checks.

### A period can be planned independently

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

### Long absence is an additional suggestion

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

### Verify the gateway contract first

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
