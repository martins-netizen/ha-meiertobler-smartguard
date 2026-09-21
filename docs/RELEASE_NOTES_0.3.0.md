# Release notes: 0.3.0

Status: published release

Published on 2026-09-21 as the annotated `v0.3.0` tag at commit
`94b7305c3fcb61b3647452637fb479735a66e8b7`. The public GitHub release is
available at
<https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/tag/v0.3.0>.
Its deterministic manual-installation bundle has SHA-256
`190b3aeb71e43fed8592242416ed5cd702bdbc9c2e82bdb279b4cea4d9209dc5`.

## What is included

- UI configuration and reconfiguration of one SmartGuard 2.0 gateway.
- Eight read-only sensor entities and one HK60 operating-mode select.
- Coordinated 60-second polling and immediate readback after every mode write.
- Redacted diagnostics that use the coordinator data already held in memory.
- A guarded night-heating blueprint with a stable source at the `v0.3.0` tag.
- Troubleshooting, automation, security, and controlled-release documentation.

The runtime control behavior is unchanged from the verified `0.2.0` baseline.
The integration still permits only the six known HK60 modes and never updates
the displayed select state optimistically.

## Compatibility

- Home Assistant `2026.9.0` or newer.
- Meier Tobler SmartGuard 2.0 with device type `1001`.
- HK60 enabled for the five HK60-specific entities.

## Installation and upgrade

The release can be added to HACS as a custom integration repository or
installed with the attached deterministic ZIP. Updating the custom component
does not change Home Assistant YAML configuration or migrate existing
automations. Restart Home Assistant after replacing the integration files.

HACS uses the tagged `custom_components/meiertobler_smartguard` source tree
because this repository does not declare `zip_release`. The attached ZIP is the
separately verified manual-installation bundle. Both originate from the same
annotated release tag. The controlled HACS test is documented in
[HACS_TEST_V0.3.0.md](HACS_TEST_V0.3.0.md).

## Known limitations

- The locally verified REST API uses unauthenticated HTTP. Keep the gateway on
  a segmented local network, allow TCP port 80 only from Home Assistant, and
  never expose the API to the internet.
- The SmartGuard UI password does not protect the REST data API and is neither
  requested nor stored by this integration.
- Only device type `1001` and the documented HK60 datapoints are verified.
- Automatic discovery and Home Assistant repair issues are not implemented.
- The blueprint source is public but must not replace production automations
  before a separate import and complete night/morning migration test.

## Publication verification

The version pull request, protected `main` validation, annotated-tag Release
Gate, deterministic bundle inspection, Home Assistant field smoke test, public
official HACS validation, release review, and publication verification all
passed. The release was published manually; the tag workflow itself retained
read-only permissions and did not publish anything automatically.

Installation through HACS as a custom repository remains a separate
post-release test and is not claimed as complete in these notes.
