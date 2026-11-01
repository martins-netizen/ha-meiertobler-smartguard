# Holiday mode and confirmed long absence

Status: **design only**. No holiday entity, schedule write, absence automation
or new gateway action is implemented by the heating-curve change.

The supplied frontend references holiday start `5226`, end `5227` and a holiday
field `5241`. Its circuit block is a template; an installation's verified active
circuit must determine the API target. The `5241` field has unit K in the HTML;
it must not be assumed to be a boolean holiday-active flag. The external
`javascript/app.js` and bounded read-only responses must establish representation,
unset values, timezone handling, activation semantics and write behavior first.
An HTML save button alone does not establish supported safe write semantics.

## Proposed Home Assistant behavior

1. Track **continuous, reliably known absence of all selected people**. A lighting
   presence simulation is a consumer of that signal, not its source: its daytime
   pause, sunset schedule or manual light switch must not count as a return.
2. After a configurable long-absence threshold (initial proposal: 24 hours),
   offer a persistent Home Assistant suggestion to prepare a holiday period.
   Unavailable presence data cannot be treated as proof of absence.
3. Ask for the intended end/return time. Show the verified circuit, existing
   schedule, proposed start/end and known effect before explicit confirmation.
   Do not invent an unlimited or repeatedly extended absence period.
4. Recheck absence, target identity and the unchanged source schedule immediately
   before any future confirmed change. Direct unconfirmed services must not
   provide a bypass around the guided change request.
5. Record ownership of only the period created by this operation. A manual
   schedule must not be overwritten. Offer an early-end confirmation when
   reliable return is detected; never clear an unrelated or subsequently edited
   period. Automatic physical activation or recovery requires an explicitly
   agreed policy compatible with the per-change confirmation requirement.

The 24-hour timer must be independent of a short lighting-simulation delay.
Persist the absence start across HA restarts, check elapsed UTC time at startup,
and use the installation timezone only for display and verified gateway encoding.
Handle DST, expired requests, late confirmation and a person returning before
confirmation. Do not silently change a room temperature, frost-protection
setting, hot-water schedule or legionella program as part of holiday support.

Integration support and a user-specific presence automation are separate steps.
Existing authorized night-mode recovery and lighting automation stay intact.
The immediate next step is a filtered **read-only** contract check. Synthetic
tests and an exact, explicitly confirmed value/period are required before any
physical write test. This document is not a live-installation acceptance report.
