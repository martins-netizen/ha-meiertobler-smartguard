# Automation examples

Use the internal SmartGuard states in YAML: `auto`, `normal`, `reduced`,
`frost_protection`, `heating` and `cooling`. Home Assistant may translate their
labels. Find the exact IDs under **Settings > Devices & services >
Meier Tobler SmartGuard > Entities**.

## Guarded night-heating blueprint

The [repository blueprint](../blueprints/automation/martins_netizen/smartguard_guarded_night_heating.yaml)
selects heating only when automatic operation is cooling and the indoor
temperature is low enough. A persistent ownership helper records a confirmed
change made by this automation. Morning recovery leaves manually selected
heating alone when that marker is off.

### Prepare the inputs

Under **Settings > Devices & services > Helpers > Create helper > Toggle**,
create **two separate Toggle helpers**. Start both off.

| Input | Select or enter |
| --- | --- |
| HK60 operating-mode select | The SmartGuard select with internal options `auto` and `heating` |
| HK60 operating-status sensor | The operating-status sensor, not selected/effective mode |
| Automatic night-heating enable helper | A toggle for enabling new night overrides |
| Night-heating ownership helper | A different toggle used exclusively by this automation |
| Indoor-temperature sensor | A representative or maximum room temperature in **°C** |
| Maximum indoor temperature | Your limit; default **25 °C**, not a heating setpoint |
| Select heating / Return to auto | Local times; defaults **23:00 / 06:00** |

Keep the ownership helper's normal state restoration. Do not configure an
`initial` value that resets it at every restart. Do not share this marker with
other automations or turn it on manually. Using the same helper for enable and
ownership prevents all actions.

### Import and create the automation

1. Open **Settings > Automations & scenes > Blueprints > Import blueprint**.
2. Paste this GitHub address, select **Preview**, then **Import blueprint**:

   https://github.com/martins-netizen/ha-meiertobler-smartguard/blob/main/blueprints/automation/martins_netizen/smartguard_guarded_night_heating.yaml

3. Choose **Create automation**, fill in the inputs above and save.
4. Keep the enable helper off while reviewing inputs and traces; turn it on
   only when you want scheduled night changes.

The URL tracks reviewed changes on `main`. Keep a copy before re-importing.
Home Assistant imports GitHub files under the owner name: the default stored
path uses **`martins-netizen/`**, with a hyphen.

This example shows a saved configuration. Replace every example entity ID:

```yaml
alias: SmartGuard - guarded night heating
use_blueprint:
  path: martins-netizen/smartguard_guarded_night_heating.yaml
  input:
    mode_select: select.replace_with_your_smartguard_mode_select
    operating_status: sensor.replace_with_your_smartguard_operating_status
    enable_helper: input_boolean.replace_with_your_night_heating_enable
    override_helper: input_boolean.replace_with_your_night_heating_owner
    indoor_temperature: sensor.replace_with_your_indoor_temperature
    maximum_indoor_temperature: 25.0
    heating_time: "23:00:00"
    auto_time: "06:00:00"
```

### What happens

| Situation | Result |
| --- | --- |
| Enable on, marker off, requested `auto`, status `cooling`, valid °C temperature at/below limit | Select `heating`; set marker only after successful service and reported `heating` |
| A night safeguard fails, temperature missing/non-finite or unit not °C | No mode change |
| Morning, marker on and mode still `heating` | Select `auto`; clear marker after reported `auto` |
| Morning, manually selected `heating` with marker off | No mode change |
| Another known mode is selected | Clear marker; preserve the selected mode |
| Select `unknown`/`unavailable` | No mode write; retain marker until mode can be read |
| Enable turned off after a confirmed night override | No new override; morning recovery of the owned change still runs |

Selecting **Heating again while Heating is already selected** produces no
distinguishable state change. To keep heating manually beyond the morning
time, turn the ownership marker **off**. A change while Home Assistant cannot
observe the gateway also cannot be reliably attributed.

If Home Assistant is stopped or the gateway is unavailable at the morning
time, there is no startup/reconnection catch-up. Inspect the actual mode and
marker and return to Auto manually if needed. A restart alone must not reset
the helper. A failed night service does not create ownership; a failed morning
return retains existing ownership. Inspect the automation trace.

### Existing automations and re-importing

The new blueprint requires the **separate ownership helper**. Older copies
returned any current `heating` mode to `auto` without recording who selected it.

Before re-importing, disable the affected blueprint automation, preserve its
inputs/YAML and resolve any active night override. Re-import, edit the existing
automation, select the new helper and review every input before enabling it.
The new required input is not migrated automatically.

HACS updates the integration, not this separate blueprint. The URL on `main`
supplies the corrected blueprint after the reviewed change is merged. Older
tagged URLs retain their older contents.

Do not operate the old YAML/REST select and the integration select concurrently;
both write SmartGuard datapoint `5004`. Keep an already working production night
automation until its replacement has been checked. Importing alone does not
replace an existing automation.

### Verification scope

Automated tests use Home Assistant's GitHub importer with mocked HTTP content,
schema/input validation, time/state triggers, helper restoration and simulated
select services. No gateway is contacted and no real operating mode is changed.

The existing production night automation has separate field evidence. These
tests do not prove a new user's UI import/setup or replacement of a production
automation. The `docs-examples` quality rule remains pending that confirmation.
See the [quality review](QUALITY_REVIEW.md).

## Notify after prolonged unavailability

This optional example waits ten minutes before reporting a connectivity problem.

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

Review diagnostics privately. The integration does not use the SmartGuard UI
password. Keep its unauthenticated HTTP API on a trusted local network.
