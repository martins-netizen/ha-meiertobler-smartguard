# Installation, updates and recovery

[Back to the overview](../README.md)

<a id="install-with-hacs"></a>

## Install with Marketplace (HA 2026.11+)

1. Open **Settings → Marketplace** and acknowledge the community-code notice
   if prompted. Search for **Meier Tobler SmartGuard** and verify
   **martins-netizen/ha-meiertobler-smartguard**.
2. Install the latest stable release. For a first installation not previously
   loaded, Marketplace opens setup without a mandatory HA restart.
3. If setup does not open, use **Settings → Devices & services → Add integration**
   and select **Meier Tobler SmartGuard**.
4. Enter the gateway hostname or IP address without a scheme, path, port or
   credentials. Keep the gateway on a trusted local network.

This project is in the default catalogue. Catalogue installs and updates do not
require GitHub authentication. HA 2026.11 automatically migrates existing HACS
repositories; do not reinstall HACS or recreate configured entries. See the
[official Marketplace guide](https://www.home-assistant.io/integrations/marketplace/).

## Older HA: install with HACS

1. Install HACS using its [official guide](https://www.hacs.xyz/docs/use/download/download/)
   if needed, then search for **Meier Tobler SmartGuard** and verify the owner.
2. Download the latest stable release and restart Home Assistant.
3. Add the integration through **Settings → Devices & services** as above.

## Custom repository

Custom registration is normally unnecessary. If the catalogue entry is absent:

- **HA 2026.11+: Settings → Marketplace → Add from link**. Connect GitHub if
  prompted (required for custom repositories), enter
  `https://github.com/martins-netizen/ha-meiertobler-smartguard`, then **Add**.
  The type is detected; select **Integration** only if asked.
- **Older HA: HACS → three-dot menu → Custom repositories**. Add the same URL
  with category **Integration**.

Adding a URL registers metadata; it does not install files. Open the entry and
install the release using the matching version-specific procedure above.

## Update

**Prefer Marketplace/HACS for routine upgrades.** The manual ZIP is an alternative;
private dashboard helpers do not update integration software. Keep a verified
HA backup and the previous known-good version.

On HA 2026.11+, install the offered release under **Settings → Updates**, then
restart using the repair notice. On older HA, open the existing HACS entry,
select **Update** and restart. Check entity availability before applying a
new dashboard. Keep the existing config entry, entity IDs and personal settings.

If older HACS does not offer the release, select **Update information**.
Refreshing metadata does not install anything. Updates to already loaded
integrations still need a restart on HA 2026.11+.

Optional storage and [operating entities](OPERATING_READINGS.md) appear after
their first valid readings. Operating-hour counters are diagnostic entities.
Missing optional modules do not block the original heat-pump and HK60 entities.

An integration update does not re-import blueprints or replace saved automations.
Before separately re-importing the night-heating blueprint, review its
[two-helper setup and ownership rules](AUTOMATION_EXAMPLES.md).

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

Marketplace/HACS installs the tagged `custom_components/meiertobler_smartguard` source.
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

Select the previous published version in the installed Marketplace/HACS entry,
if offered, or restore a verified backup,
then restart. Additional entities introduced by the newer version may stop
providing data. Keep the existing config entry and settings when rolling back.

Changing integration files does **not** undo a holiday period already stored
in the gateway. Before the first holiday write, retain the previous complete
period. After a partial or interrupted write, inspect both dates and the mode
directly in SmartGuard. Review and explicitly confirm any corrective change;
do not assume that downgrading or removing the integration restores device data.

## Removal

Remove the config entry under **Settings → Devices & services**. For a
Marketplace/HACS installation, use its software removal action and restart
(Marketplace provides a restart repair). For a manual installation,
remove `custom_components/meiertobler_smartguard` and restart. Review dependent
automations and dashboards before removal.
