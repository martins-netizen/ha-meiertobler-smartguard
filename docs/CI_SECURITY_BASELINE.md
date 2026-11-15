# Automated quality and security baseline

This document records the automated controls shipped in published **0.8.0**
and the dated verification evidence below. Local checks, hosted PR checks,
actual merge checks, publication and owner-authenticated GitHub inventories
remain separate evidence. None establishes physical heating acceptance or a
complete security clearance.

## Reference and scope

The comparison uses `martins-netizen/ha-meteoswiss` development
`29d9bc73b2ad0dedc91c73cf167f46223330d22a` on 2026-11-15. Its
[CI](https://github.com/martins-netizen/ha-meteoswiss/blob/29d9bc73b2ad0dedc91c73cf167f46223330d22a/.github/workflows/ci.yml),
[CodeQL](https://github.com/martins-netizen/ha-meteoswiss/blob/29d9bc73b2ad0dedc91c73cf167f46223330d22a/.github/workflows/codeql.yml),
[daily audit](https://github.com/martins-netizen/ha-meteoswiss/blob/29d9bc73b2ad0dedc91c73cf167f46223330d22a/.github/workflows/dependency-audit.yml)
and [coverage gate](https://github.com/martins-netizen/ha-meteoswiss/blob/29d9bc73b2ad0dedc91c73cf167f46223330d22a/scripts/check_quality_coverage.py)
are the engineering reference. SmartGuard retains its own runtime and native uv
project; no weather runtime or unrelated feature is imported.

| Control | MeteoSwiss reference | SmartGuard 0.8.0 |
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

The recheck against the original MeteoSwiss reference
`b6c4502e5cdeb48121be628fdb7eda579df4f7c3` found unchanged CI, CodeQL, daily-audit
and dependency-lock configuration. Its coverage checker adds four HGT modules
to the existing critical-module list. SmartGuard already requires complete
statement and branch coverage for every integration module, including future
modules; no reduced threshold or unrelated weather feature is needed.

## Recorded verification and remaining operational limits

The following records apply to the named 0.8.0 source and check times:

- [PR #61](https://github.com/martins-netizen/ha-meiertobler-smartguard/pull/61)
  passed all nine hosted checks from the expected apps on
  `7df519f4c3a1ef229f8bd687747847b2f3569eca` before owner-approved merge.
- The actual merge `02bf2a6b1dceca01d4d4c99ae1080cadb9b93a77` retains the exact
  reviewed tree `7faec545a471180de997ff0ae258302e19456258` and a valid GitHub
  signature. [Main validation](https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/runs/43742930107)
  passed both full HA suites, CodeQL, the advisory audit, Quality, Hassfest and
  HACS. SonarCloud and both native dependency-graph submissions also passed.
- The annotated `v0.8.0` tag points to that merge. All four jobs in
  [Release Gate 43745963444](https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/runs/43745963444)
  passed. Each HA suite passed **590 tests and 26 subtests**, covering all
  **811 statements and 178 branches** across 15 integration modules. Strict
  MyPy passed for 19 files. Five known upstream warnings remain visible.
  The tagged advisory audit checked 149 pairs with zero active advisories and
  zero unknown results.
- [0.8.0](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/tag/v0.8.0)
  was published as stable Latest on **2026-11-15 at 18:28:49 UTC**. Both public
  assets were downloaded independently after publication; all 23 ZIP members
  match the selected source. The 51,103-byte ZIP SHA-256 is
  `f7678cf2135c7fb4a25297c0125b65b4789bb27958896c472e12e22f30d69eb3`.

The owner's authenticated inventory at **2026-11-15 17:36 UTC** confirmed
Dependabot alerts and automatic security updates, secret scanning, push
protection and private vulnerability reporting. These five settings matched
the MeteoSwiss reference. Both repositories then had zero open Dependabot and
secret alerts; the checked SmartGuard PR analysis and MeteoSwiss default-branch
analysis also had zero open code-scanning alerts. This is a dated owner check,
not a claim that public GitHub App access can inspect every setting or that
later alerts cannot appear. The configured daily schedule is distinct from an
independently observed scheduled run.

Installation, Marketplace/blueprint UI evidence and physical heating acceptance
remain separate. Open discovery and blueprint evidence in the quality review
is retained; these automated checks do not close it or constitute a Gold award.

The SmartGuard gateway API used by this integration remains unauthenticated
local HTTP and can affect heating. MeteoSwiss reads weather providers through
HTTPS; the deployments therefore have different inherent risks. The software
controls above do not remove the gateway's manufacturer-side transport limit.
Keep segmentation and restrictive HA-to-gateway access as required by
[SECURITY.md](../SECURITY.md). Existing write allowlists, identity/source checks,
explicit holiday confirmation and readback remain unchanged. No production
gateway operation is part of these CI changes.
