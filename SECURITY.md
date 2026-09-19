# Security policy

## Supported versions

Only the most recent development release is supported before version `1.0.0`.

## Reporting a vulnerability

Please do not publish vulnerabilities, credentials, diagnostics, internal IP
addresses, serial numbers, or other private installation data in a public issue.
Use GitHub Private Vulnerability Reporting after the repository is published.

Until then, contact the repository owner privately. A report should describe the
affected version, impact, and a minimal reproduction using synthetic data.

## Known transport limitation

Version `0.2.0` uses the gateway's unauthenticated local HTTP REST API. Network
segmentation and a restrictive firewall rule from Home Assistant to the gateway
are required compensating controls. The API must never be exposed to the
internet.
