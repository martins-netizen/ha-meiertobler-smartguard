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

### 1. Create the two helpers

Under **Settings > Devices & services > Helpers > Create helper > Toggle**,
create **two separate Toggle helpers**:

1. **SmartGuard Blueprint – Freigabe**: permits new automatic night changes.
2. **SmartGuard Blueprint – Nachtmerker**: remembers a confirmed change made by
   this automation so it can return that change to Auto in the morning.

Start **both off**. Use a new, dedicated marker for each automation. The
blueprint selects existing helpers; it does not create them for you.

Keep the marker's normal state restoration. If you create helpers in YAML,
omit an `initial` value that would reset the marker at every restart. Use
different helpers for the two fields. The automation manages the marker;
leave it off during setup.

### 2. Import the blueprint

1. Open **Settings > Automations & scenes > Blueprints > Import blueprint**.
2. Paste this GitHub address, select **Preview**, then **Import blueprint**:

   https://github.com/martins-netizen/ha-meiertobler-smartguard/blob/main/blueprints/automation/martins_netizen/smartguard_guarded_night_heating.yaml

3. Choose **Create automation** to open the configuration form.

Importing and opening this form is enough for an initial visual check. You can
leave the editor without saving an automation. Keep an existing working night
automation while reviewing this separate example.

### 3. Fill in the numbered form sections

The form uses German labels and includes its helper-creation instructions.
Follow the sections in order:

1. **Zwei Helfer vorbereiten**: select the two helpers created above.
2. **SmartGuard auswählen**: select the operating-mode control and current
   operating-status sensor from the same SmartGuard device.
3. **Raumtemperatur prüfen**: select a room-temperature sensor and review the
   temperature limit.
4. **Schaltzeiten (optional)**: expand this section only to change the default
   times, **23:00 / 06:00**, in Home Assistant's configured time zone.

| Form field | Select or enter |
| --- | --- |
| Freigabeschalter | **SmartGuard Blueprint – Freigabe**, initially off |
| Nachtmerker | **SmartGuard Blueprint – Nachtmerker**, initially off; dedicated to this automation |
| Betriebsmodus einstellen | The SmartGuard select, labelled **HK60 Betriebsmodus einstellen** in German, with internal options `auto` and `heating` |
| Aktueller Betriebsstatus | The operating-status sensor, labelled **HK60 Betriebsstatus** in German; its states include heating and cooling |
| Raumtemperaturfühler | A representative or maximum room-temperature sensor in **°C** |
| Temperaturgrenze für den Nachtwechsel | Your permission limit; default **25 °C**, including equality. SmartGuard continues to regulate the heating; this is not a room-temperature setpoint. |
| Nachts auf Heizen wechseln um | Local time; default **23:00** |
| Morgens zurück auf Auto um | Local time; default **06:00** |

Both helpers, the SmartGuard entities and the temperature sensor require a
selection. The temperature limit and times already have defaults. Using the
same helper for enable and ownership prevents all actions.

### 4. Save when ready to use the automation

Save a new automation with the two helpers still off. Review all inputs and
coordinate any replacement of an existing night automation before turning the
**Freigabe** helper on. Two active night controllers must not compete over the
same mode select. Existing production automations are not replaced by an import.

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

The guided German form changes labels and input grouping only. Existing input
keys, selectors, defaults, conditions and actions remain the same as the
ownership-aware version. Saved inputs remain compatible. Re-import from the
Blueprints menu to receive the form update; a HACS integration update does not
update a separately imported blueprint. Review the inputs after re-importing.

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
