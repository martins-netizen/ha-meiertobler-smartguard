# Automation examples

These examples use Home Assistant's current automation syntax and the stable
internal SmartGuard values. Home Assistant may translate the values for display,
but YAML must use `auto`, `normal`, `reduced`, `frost_protection`, `heating`, or
`cooling` exactly as shown.

Before using an example, replace every example entity ID with the ID from your
own installation. Find the exact IDs under **Settings > Devices & services >
Meier Tobler SmartGuard > Entities**. Test a copied automation manually and
inspect its trace before relying on a schedule.

During migration, do not operate the old YAML/REST select and the integration
select concurrently. Both control SmartGuard datapoint `5004`.

## Prepared guarded-night-heating blueprint

The repository contains a tested
[guarded night-heating blueprint](../blueprints/automation/martins_netizen/smartguard_guarded_night_heating.yaml).
It combines the two scheduled mode changes with the following safeguards:

- night heating runs only while a selected input boolean is on;
- the requested mode must still be `auto`;
- the operating status must be `cooling`;
- the selected indoor-temperature sensor must be at or below the configured
  limit; and
- the morning action returns to `auto` only if the requested mode is still
  `heating`.

The blueprint is source-controlled and validated, but it is not published while
this repository remains private. Do not replace the existing production
automations with it yet. After publication, it must be imported into a test Home
Assistant instance, linked from the public documentation, and tested through a
complete night/morning cycle before migration.

## Select heating at night only when cooling is active

This guarded example changes from automatic operation to heating only when the
current requested mode is `auto` and the operating status is `cooling`. It does
not overwrite another manually selected mode.

```yaml
alias: SmartGuard - select heating at night
description: Select heating only when automatic operation is currently cooling.
triggers:
  - trigger: time
    at: "23:00:00"
conditions:
  - condition: state
    entity_id: select.replace_with_your_smartguard_mode_select
    state: "auto"
  - condition: state
    entity_id: sensor.replace_with_your_smartguard_operating_status
    state: "cooling"
actions:
  - action: select.select_option
    target:
      entity_id: select.replace_with_your_smartguard_mode_select
    data:
      option: "heating"
mode: single
```

## Return to automatic operation without overwriting another mode

This example returns to `auto` only when the select still contains the
automation's expected `heating` value. A later manual selection therefore wins.

```yaml
alias: SmartGuard - return to automatic operation
description: Return to auto only when the guarded night mode is still active.
triggers:
  - trigger: time
    at: "06:00:00"
conditions:
  - condition: state
    entity_id: select.replace_with_your_smartguard_mode_select
    state: "heating"
actions:
  - action: select.select_option
    target:
      entity_id: select.replace_with_your_smartguard_mode_select
    data:
      option: "auto"
mode: single
```

## Create a persistent notification after prolonged unavailability

This example reports a connectivity problem only after the entity has remained
unavailable for 10 minutes, avoiding a notification for a single missed poll.

```yaml
alias: SmartGuard - report prolonged unavailability
description: Notify after the SmartGuard mode select is unavailable for 10 minutes.
triggers:
  - trigger: state
    entity_id: select.replace_with_your_smartguard_mode_select
    to: "unavailable"
    for: "00:10:00"
conditions: []
actions:
  - action: persistent_notification.create
    data:
      title: "SmartGuard unavailable"
      message: >-
        The SmartGuard operating-mode select has been unavailable for 10 minutes.
        Check the local network and the integration diagnostics.
mode: single
```

## Safety notes

- Keep state conditions immediately before every write so an automation does
  not silently replace a manual choice.
- Use automation traces to determine which automation performed a write.
- Never put a SmartGuard password in automation YAML. This integration does not
  use or store one.
- Keep the gateway REST API on the local network and do not expose it to the
  internet.
- The repository blueprint is not yet publicly importable. Publication, a
  stable public link, and an end-to-end test are still required before claiming
  the Home Assistant `docs-examples` quality rule.
