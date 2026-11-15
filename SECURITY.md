# Security policy

## Supported versions

Only the most recent published release is supported before version `1.0.0`.
Each release declares its minimum Home Assistant Core version in `hacs.json`.
Use a Core release with current security fixes. See the
[installation and upgrade guide](docs/INSTALLATION.md) for the supported
minimum and the upgrade order.

## Reporting a vulnerability

Please do not publish vulnerabilities, credentials, diagnostics, internal IP
addresses, serial numbers, or other private installation data in a public issue.
Use GitHub Private Vulnerability Reporting when the repository offers that
option. If no private reporting form is available, open only a minimal public
issue requesting private contact and include no vulnerability details or
installation data. A private report should describe the affected version,
impact, and a minimal reproduction using synthetic data.

## Known transport limitation

SmartGuard uses the gateway's unauthenticated local HTTP REST API. Network
segmentation and a restrictive firewall rule from Home Assistant to the gateway
are required compensating controls. The API must never be exposed to the
internet.

## Release safeguards

Every external GitHub Action is pinned to a full commit SHA. Workflows keep
repository contents read-only, do not use the privileged `pull_request_target`
event, and never publish automatically. Only the CodeQL analysis job receives
`security-events: write` to upload findings; it cannot write repository contents.
The protected Quality check requires both complete HA suites, 100% statement
and branch coverage for every integration module, CodeQL and the complete
dependency advisory audit. Active advisories or unknown/malformed results fail
the audit; there are no ignore or alternate-registry switches. The audit also
runs daily against the universal lock, including foreign-platform selections.
The release gate
accepts only an annotated stable-version tag on a commit contained in `main`,
checks version consistency, requires both full HA suites and a clean dependency
audit before building, and emits a
SHA-256 checksum for the deterministic release bundle.

See the [baseline and evidence limits](docs/CI_SECURITY_BASELINE.md). A clean
advisory lookup is specific to its source and time; it is not a guarantee that
all vulnerabilities are known. GitHub alert/settings inventories and deployment
network controls require their own current evidence.
