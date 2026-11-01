# Scheduled holidays, heating and presence simulation

Status: **design only**. No holiday entity, schedule write, presence automation
or new gateway action is implemented by the heating-curve change.

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

Bounded read-only replies and the actual referenced frontend script must
establish timestamp units, timezone handling, unset values, activation rules
and supported write behavior. The static script URL must be resolved from the
observed document/base, not guessed at the gateway root. An HTML save button
alone is not proof of safe write semantics. No real planned absence dates,
personal identities or raw device data should be published as evidence.

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
