# Release notes: 0.3.0

Status: unpublished release candidate

No tag or GitHub release has been created. These notes prepare the candidate
for review; they do not publish it or make the private repository available to
HACS.

## What is included

- UI configuration and reconfiguration of one SmartGuard 2.0 gateway.
- Eight read-only sensor entities and one HK60 operating-mode select.
- Coordinated 60-second polling and immediate readback after every mode write.
- Redacted diagnostics that use the coordinator data already held in memory.
- A guarded night-heating blueprint for review and test use after publication.
- Troubleshooting, automation, security, and controlled-release documentation.

The runtime control behavior is unchanged from the verified `0.2.0` baseline.
The integration still permits only the six known HK60 modes and never updates
the displayed select state optimistically.

## Compatibility

- Home Assistant `2026.9.0` or newer.
- Meier Tobler SmartGuard 2.0 with device type `1001`.
- HK60 enabled for the five HK60-specific entities.

## Upgrade preparation

Until publication, install this candidate only through the existing controlled
manual deployment process. Updating the custom component does not change the
Home Assistant YAML configuration or migrate existing automations. Restart Home
Assistant after replacing the integration files.

HACS installation and update testing can begin only after the repository is
made public and a full GitHub release is deliberately published. The prepared
blueprint is not yet available from a stable public import URL.

## Known limitations

- The locally verified REST API uses unauthenticated HTTP. Keep the gateway on
  a segmented local network, allow TCP port 80 only from Home Assistant, and
  never expose the API to the internet.
- The SmartGuard UI password does not protect the REST data API and is neither
  requested nor stored by this integration.
- Only device type `1001` and the documented HK60 datapoints are verified.
- Automatic discovery and Home Assistant repair issues are not implemented.
- The blueprint remains unpublished and must not replace production
  automations before a separate end-to-end migration test.

## Candidate gates

Before tagging this version:

1. Review and merge the version pull request only after Quality, Hassfest, and
   HACS checks pass.
2. Confirm the exact merged `main` commit and its final Validate run.
3. Create an annotated `v0.3.0` tag only after explicit approval.
4. Run the read-only Release Gate, inspect its deterministic ZIP and checksum,
   and complete a Home Assistant smoke test.
5. Keep the repository private unless publication is separately approved.

A future GitHub release must be created manually from the approved tag. Pushing
the tag or passing the gate does not publish a GitHub release.
