# Troubleshooting

Start with the symptom that matches what Home Assistant shows. Do not post a
SmartGuard password, internal IP address, serial number, global device
identifier, or unreviewed diagnostics in an issue.

## The integration cannot connect during setup

### Symptom

The setup form reports that the SmartGuard gateway cannot be reached.

### Description

Home Assistant could not read the verified local HTTP API within the request
timeout. A SmartGuard gateway may still serve HTTP even when it does not answer
ping, so a failed ping alone does not prove that the gateway is offline.

### Resolution

1. Enter only the gateway hostname or IP address. Do not include `http://`, a
   path, a port, a username, or a password.
2. Confirm that Home Assistant and the gateway can communicate over local TCP
   port 80. Check VLAN routing and firewall rules in both directions.
3. From a trusted host on the Home Assistant network, test whether the gateway
   answers an HTTP request. Do not expose the API to the internet.
4. Confirm that the gateway address has not changed. If an existing entry uses
   an old address, use **Settings > Devices & services > Meier Tobler
   SmartGuard > Reconfigure**.
5. Restart the gateway only if this is safe for the heating system, then retry
   setup.

## The device type is not supported

### Symptom

Setup reaches the gateway but reports an unsupported device.

### Description

Version `0.2.0` accepts only the locally verified SmartGuard 2.0 device type
`1001`. Refusing another type prevents the integration from guessing API paths
or writing to an unverified controller.

### Resolution

Do not work around the check. Open a bug report with the Home Assistant version,
integration version, SmartGuard model, and sanitized diagnostics. Remove all
addresses and device identifiers before submitting them.

## Entities are unavailable

### Symptom

One or more SmartGuard entities show `unavailable` after they previously worked.

### Description

The coordinator marks entities unavailable when the scheduled gateway update
fails. The integration retries automatically on the next 60-second update.

### Resolution

1. Wait for at least one complete update interval.
2. Confirm local TCP port 80 connectivity from Home Assistant to the gateway.
3. Check whether the gateway address or network segmentation changed.
4. Enable debug logging from the SmartGuard integration entry, reproduce one
   failed update, and disable debug logging again.
5. Download diagnostics from the integration entry and review them before
   sharing. The integration redacts the configured host, global device
   identifier, and serial number, but the user remains responsible for checking
   the complete file.

## A selected operating mode is rejected or changes back

### Symptom

Home Assistant reports that the write failed or was not confirmed, or the mode
returns to its earlier value.

### Description

The integration writes only a verified option and immediately reads datapoint
`5004` back. It reports an error when the gateway does not confirm the requested
value. A second automation, the old YAML/REST select, or the SmartGuard user
interface can also write the same physical datapoint.

### Resolution

1. Check that the requested option is one of `auto`, `normal`, `reduced`,
   `frost_protection`, `heating`, or `cooling`.
2. During migration, do not let the old YAML/REST select and the integration
   select control the datapoint concurrently.
3. Review Home Assistant automation traces around the failed write and disable
   competing automations temporarily.
4. Retry once from the integration select. If readback still fails, collect
   sanitized diagnostics and debug logs for a bug report.

## The SmartGuard password is not requested

### Symptom

The setup form asks only for a host even though a password is configured in the
SmartGuard user interface.

### Description

The locally verified REST data API is unauthenticated. The SmartGuard user
interface password does not protect that endpoint, and the integration neither
uses nor stores it.

### Resolution

This is expected for version `0.2.0`. Keep the gateway on a segmented local
network, restrict TCP port 80 to the Home Assistant host, and never forward the
gateway API to the internet.

## Home Assistant reports that the device is already configured

### Symptom

A second setup attempt is aborted as already configured.

### Description

The integration uses the gateway's global device identifier as its unique
identity. This prevents duplicate config entries when the hostname or IP address
changes.

### Resolution

Use **Reconfigure** on the existing integration entry to change its address.
Remove and recreate the entry only when reconfiguration cannot recover it.

## Preparing a useful bug report

Before opening an issue:

1. install the newest available integration version;
2. reproduce the problem once with debug logging enabled;
3. disable debug logging;
4. download diagnostics and inspect the complete file;
5. replace any installation-specific values in pasted excerpts with synthetic
   values; and
6. describe the exact steps, expected result, actual result, and time of the
   failure.

Never publish credentials, internal addresses, serial numbers, global device
identifiers, full unreviewed diagnostics, or data belonging to another system.
