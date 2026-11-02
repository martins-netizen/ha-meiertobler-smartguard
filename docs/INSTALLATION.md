# Installation, updates and recovery

[Back to the overview](../README.md)

## Install with HACS

1. Open HACS and search for **Meier Tobler SmartGuard**.
2. Download the latest stable release and restart Home Assistant.
3. Open **Settings → Devices & services → Add integration** and select
   **Meier Tobler SmartGuard**.
4. Enter the gateway hostname or IP address, without a scheme, path, port or
   credentials. Keep the gateway on a trusted local network.

The integration is in the default HACS catalogue. Adding it as a custom
repository is normally unnecessary.

## Custom repository

If needed, open **HACS → three-dot menu → Custom repositories**, add
`https://github.com/martins-netizen/ha-meiertobler-smartguard` with category
**Integration**, then download and restart as above. Adding the repository
registers metadata; it does not itself install integration files.

## Update

**Prefer HACS for routine upgrades.** The manual ZIP is an alternative;
private dashboard helpers do not update the integration. Install the published
HACS update and restart HA before applying a dashboard that needs new entities.

Keep a verified Home Assistant backup and the previous known-good version.
Open the existing HACS entry, select **Update**, restart Home Assistant and
check entity availability. Keep the existing config entry, entity IDs and
personal settings; do not remove and recreate the integration.

If the new release is missing, select **Update information** and check again.
The available version and the installed version are different states: refreshing
metadata does not install anything.

Optional storage and [operating entities](OPERATING_READINGS.md) appear after
their first valid readings. Operating-hour counters are diagnostic entities.
Missing optional modules do not block the original heat-pump and HK60 entities.

An integration update does not re-import blueprints or replace saved
automations. Before separately re-importing the night-heating blueprint, review
its [two-helper setup and ownership rules](AUTOMATION_EXAMPLES.md).

## Enter holiday dates

The dashboard timestamp entities are read-only. Open **Settings → Devices &
services → Meier Tobler SmartGuard**, then use the **Configure gear beside the
existing gateway entry**. The three-dot **Reconfigure** action changes the host;
it does not open the holiday editor. Choose both dates, review the old/new and
intermediate periods, and explicitly confirm. Opening the editor writes nothing.
If the gear is missing immediately after updating files, restart HA to load the
new flow. Keep the existing config entry.

## Manual installation

1. Open the [latest stable release](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/latest).
2. Download the attached `meiertobler_smartguard-<version>.zip` and its `.sha256`
   file. Verify the ZIP against the checksum for that same version.
3. Extract it into the Home Assistant configuration directory, preserving
   `custom_components/meiertobler_smartguard`.
4. Restart Home Assistant, then add the integration as described above if this
   is a new installation.

HACS installs the tagged `custom_components/meiertobler_smartguard` source.
The attached deterministic ZIP is a separate manual-installation bundle;
`hacs.json` does not enable `zip_release`. GitHub's automatic source archives
are different from that bundle.

## Existing YAML/REST installations

Migrate automation and dashboard references, including their state/option
values, before removing old definitions. Keep a verified backup and confirm the
new entities first. Both old and new mode selects control the same physical
setting; do not operate them concurrently. Do not remove unrelated helpers or
automations as part of installing this integration.

## Rollback

Select the previous published version in HACS or restore a verified backup,
then restart. Additional entities introduced by the newer version may stop
providing data. Keep the existing config entry and settings when rolling back.

Changing integration files does **not** undo a holiday period already stored
in the gateway. Before the first holiday write, retain the previous complete
period. After a partial or interrupted write, inspect both dates and the mode
directly in SmartGuard. Review and explicitly confirm any corrective change;
do not assume that downgrading or removing the integration restores device data.

## Removal

Remove the config entry under **Settings → Devices & services**. For a HACS
installation, use its removal action and restart. For a manual installation,
remove `custom_components/meiertobler_smartguard` and restart. Review dependent
automations and dashboards before removal.
