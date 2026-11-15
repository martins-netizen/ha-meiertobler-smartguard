# Automated quality and security baseline

This document describes the proposed 0.8.0 source configuration. Successful
local checks, hosted checks on the exact PR head, actual merge checks and
owner-authenticated GitHub settings/alert inventories are separate evidence.
Do not infer publication, field acceptance or a complete security clearance
from this configuration alone.

## Reference and scope

The comparison uses `martins-netizen/ha-meteoswiss` development
`b6c4502e5cdeb48121be628fdb7eda579df4f7c3` on 2026-11-15. Its
[CI](https://github.com/martins-netizen/ha-meteoswiss/blob/b6c4502e5cdeb48121be628fdb7eda579df4f7c3/.github/workflows/ci.yml),
[CodeQL](https://github.com/martins-netizen/ha-meteoswiss/blob/b6c4502e5cdeb48121be628fdb7eda579df4f7c3/.github/workflows/codeql.yml),
[daily audit](https://github.com/martins-netizen/ha-meteoswiss/blob/b6c4502e5cdeb48121be628fdb7eda579df4f7c3/.github/workflows/dependency-audit.yml)
and [coverage gate](https://github.com/martins-netizen/ha-meteoswiss/blob/b6c4502e5cdeb48121be628fdb7eda579df4f7c3/scripts/check_quality_coverage.py)
are the engineering reference. SmartGuard retains its own runtime and native uv
project; no weather runtime or unrelated feature is imported.

| Control | MeteoSwiss reference | SmartGuard candidate |
| --- | --- | --- |
| HA compatibility | Complete 2026.11.0 and 2026.11.1 suites | Both complete suites with matching official fixtures |
| Required security analysis | CodeQL plus separately checked SonarCloud | CodeQL required through Quality; SonarCloud retained and verified separately |
| Dependency advisories | Complete universal locks, required in CI, daily audit | Every registry record in the native universal lock, required in CI, identical daily audit |
| Unknown advisory results | Fail closed | Fail closed; no ignore, skip-unknown or alternate-index switch |
| Coverage regression gate | All modules above 95%, total at least 99%, listed critical modules at 100% | Every integration Python module at 100% statements and branches, including new modules |
| Typing and linting | No equivalent strict MyPy CI gate | Existing full-integration strict MyPy and Ruff retained; security/coverage helpers also checked |
| Dependency integrity | Hash-pinned fixtures, reviewed security floors | Hash-pinned native fixture/build exports, same floors plus multidict 6.9.1 |
| Token scope | Contents read-only; CodeQL security-result upload | Same narrow exception; no contents-write or privileged PR trigger |
| Review and publication | Reviewed source and actual-merge checks | Exact-head trusted checks, normal merge, actual-merge verification, annotated-tag Release Gate and deterministic assets |

This is a comparison of specific controls, not a score based on test counts.
Neither custom integration has an official Home Assistant Gold certification.
Open discovery and blueprint UI evidence in
[the quality review](QUALITY_REVIEW.md) remains open.

## One native universal lock, two complete environments

`ci/pyproject.toml` declares the minimum fixture in `ci` and the current fixture
in `ci-current`. uv's documented mutually exclusive groups resolve both exact
HA pins in one `ci/uv.lock`. All platforms remain represented; no `environments`
restriction or Linux-only export is introduced. Select exactly one fixture
group when exporting; retain the common build group and the existing
hash-checking, wheel-default and pyric-only source-build policy.

Regression checks export each group offline with an empty uv cache and verify
Linux, macOS and Windows selections, exact pins and hashes. The actual pinned
uv binary is also probed against a local HTTP detector: offline mode must make
no request, while the same command's controlled online run reaches only that
local detector. Compatibility jobs use `UV_OFFLINE=true` throughout.

The native Dependabot directory and lockfile-only policy remain `/ci`; fixture
pins still change only in a coordinated review. The earlier successful hosted
PR-creation result remains specific to that repository/path; it does not
identify GitHub's internal rejection rule. Future hosted updates must be
reviewed against both fixture groups and all universal selections.

## Fail-closed advisory audit

The reviewed MeteoSwiss transport/metadata checker and its adversarial tests
are reused with a native uv inventory reader. The reader includes every
registry package/version pair without evaluating platform or group markers.
It validates the expected virtual project, PyPI registry, exact versions and
archive hash structure; unsupported sources and incomplete locks fail before
a query. Identical name/version pairs are queried once, retaining their lock
association. The current lock contains 150 records: one virtual project and
149 registry pairs, including both HA/fixture versions.

Only fixed-origin PyPI HTTPS release metadata is requested. TLS validation,
hostname checks, no redirects, no application credentials, bounded responses,
timeouts, worker count and one bounded retry are retained. Malformed or
duplicate JSON, mismatched releases, missing inventories, future/invalid
withdrawals and transport errors cannot be reported as clean. The tests
include real in-memory TLS handshakes for trust, hostname and date failures.

The same steps run on PRs/main, tagged release validation and daily at 05:17
UTC. An active advisory or unknown result fails the job. Quality depends on
both full HA environments, CodeQL and the audit and uses `always()` with
explicit successful-result checks; skipped or cancelled jobs cannot pass it.
The existing protected Quality context therefore enforces the added scans
without relaxing or replacing its ruleset. The release bundle is produced
only after both full suites and the advisory job succeed and the annotated
tag, exact source and main ancestry are verified.

PyPI's advisory inventory is one source at one time. A zero result does not
prove that all vulnerabilities are known. Dependabot, CodeQL, SonarCloud and
owner-authenticated GitHub alert/settings checks remain complementary.

## Remaining operational evidence and risk

After publishing the candidate branch, verify all eight trusted checks on
its exact head. Keep the production installation, existing tags and releases
unchanged until the normal merge/release decisions. Re-read the actual merge
results before selecting a publication source.

Verify the owner's current Dependabot alerts/security updates, secret scanning,
push protection and open alert inventories separately. A GitHub App that
cannot read a setting does not establish that it is enabled or clean.

The SmartGuard gateway API used by this integration remains unauthenticated
local HTTP and can affect heating. MeteoSwiss reads weather providers through
HTTPS; the deployments therefore have different inherent risks. The software
controls above do not remove the gateway's manufacturer-side transport limit.
Keep segmentation and restrictive HA-to-gateway access as required by
[SECURITY.md](../SECURITY.md). Existing write allowlists, identity/source checks,
explicit holiday confirmation and readback remain unchanged. No production
gateway operation is part of these CI changes.
