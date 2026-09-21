# Security policy

## Supported versions

Only the most recent published release is supported before version `1.0.0`.

## Reporting a vulnerability

Please do not publish vulnerabilities, credentials, diagnostics, internal IP
addresses, serial numbers, or other private installation data in a public issue.
Use GitHub Private Vulnerability Reporting when the repository offers that
option. If no private reporting form is available, open only a minimal public
issue requesting private contact and include no vulnerability details or
installation data. A private report should describe the affected version,
impact, and a minimal reproduction using synthetic data.

## Known transport limitation

Version `0.3.0` uses the gateway's unauthenticated local HTTP REST API. Network
segmentation and a restrictive firewall rule from Home Assistant to the gateway
are required compensating controls. The API must never be exposed to the
internet.

## Release safeguards

Every external GitHub Action is pinned to a full commit SHA. Validation and
release workflows use a read-only `GITHUB_TOKEN`, do not use the privileged
`pull_request_target` event, and never publish automatically. The release gate
accepts only an annotated stable-version tag on a commit contained in `main`,
checks version consistency, repeats the complete test suite, and emits a
SHA-256 checksum for the deterministic release bundle.
