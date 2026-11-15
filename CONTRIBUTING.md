# Contributing

The project is public and uses controlled development after its first release.
Changes use a feature, fix, or documentation branch and a pull request into
`main`. The active repository ruleset blocks direct changes to `main` and
requires the Quality, Hassfest, and HACS checks.

Before opening a pull request:

1. run `python3 scripts/validate.py`;
2. run Ruff, MyPy, and the complete test suite as documented in the
   [development checks](docs/TECHNICAL_REFERENCE.md#development-checks);
3. update the README and affected guides with compatibility, upgrade steps, and
   release scope when those change;
4. verify that no private installation data are present;
5. describe any security impact in the pull-request template.

Do not include credentials, internal network details, real device identifiers,
or exported diagnostics. Use synthetic identifiers and addresses from the
documentation ranges such as `192.0.2.0/24`.

Dependency updates are reviewed through normal pull requests. They are never
merged automatically.

## CI dependency updates

The CI and Release Gate environment uses the official
[`pytest-homeassistant`](https://github.com/home-assistant/core/tree/2026.11.0/packages/pytest-homeassistant)
package, pinned to **2026.11.0** for the advertised minimum and **2026.11.1**
for the current target. The protected **Quality** check requires both complete
integration/blueprint suites, CodeQL and the complete dependency advisory audit.
Keep minimum HA and fixture versions aligned with `hacs.json`; change each
explicit fixture pin only in a coordinated baseline review.

The canonical validation project is [`ci/pyproject.toml`](ci/pyproject.toml)
and its universal [`ci/uv.lock`](ci/uv.lock). The `ci` group contains the minimum
fixture and tools; `ci-current` contains the matching current fixture and the
same tools. The groups are explicitly mutually exclusive using uv's
[documented conflicts](https://docs.astral.sh/uv/concepts/resolution/#conflicting-dependencies).
Export and install each in a separate environment; do not use `--all-groups`.
The shared `build` group contains preinstalled build tools. HA supplies compatible versions of
pytest, pytest-asyncio, aiohttp, yarl and uv through its dependency graph.
Security constraints retain the certifi, multidict and uv minimums.

Dependabot uses native uv lockfile updates with `versioning-strategy:
lockfile-only`. Weekly update PRs stay inside the reviewed manifest constraints;
the exact HA fixture pins therefore change only with a coordinated baseline
review. Alerts remain enabled and no dependency is ignored. A security fix that
requires relaxing an HA pin needs a reviewed HA/fixture baseline change; this
policy cannot make an incompatible version safe to install.

Keep the validation manifest and lockfile together in `ci/`. Workflow YAML and
`dependabot.yml` retain their standard locations under `.github/`. The separate
CI project uses this layout as a compatibility workaround for the hosted
PR-creation rejection reported for dependency projects under `.github/` in
[Dependabot issue #15721](https://github.com/dependabot/dependabot-core/issues/15721).
A [comparable uv project](https://github.com/davisbuilds/skilleval/pull/2) produced
a [real Dependabot PR after relocation](https://github.com/davisbuilds/skilleval/pull/3).
The repository-specific workaround was verified after
[PR #59](https://github.com/martins-netizen/ha-meiertobler-smartguard/pull/59):
[hosted uv run 43717927120](https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/runs/43717927120)
received HTTP 204 when creating
[PR #60](https://github.com/martins-netizen/ha-meiertobler-smartguard/pull/60).
That reviewed update was merged with all checks passing. This result does not
identify GitHub's internal rejection rule or establish a general upstream fix.
After future updater-layout changes, require another actual update PR;
repository CI alone cannot prove hosted PR creation. If an update job fails,
use the focused lock-update procedure below through a normal reviewed PR.
Keep alerts and existing permissions intact.

Validate and Release Gate install uv through the full-SHA-pinned official
`setup-uv` action, reading its exact version from the CI lock. They export the
`build` and the selected `ci`/`ci-current` group with `uv export --locked --offline` into runner-temporary
requirements files. Exported requirements include hashes and platform markers.
No second requirements lockfile is committed or independently maintained.

Creating a lock after changing constraints needs registry access for every
supported platform, even on a different host OS. Do not force this resolution
offline. Once the canonical lock is current, CI consumes it offline; regression
tests verify those exports with an empty uv cache.

Both workflows install wheels by default. The source-build exception is
`pyric`, whose pinned version provides a source archive. It must match the
exported SHA-256 hashes. Builds use `--no-build-isolation` and `--no-deps`, so
pip does not automatically fetch additional build tools or dependencies.
The build group is installed first, and `pip check` verifies the final set.
Review the source-build exception whenever the pyric pin changes.

For a focused tool update, use `uv lock --directory ci --upgrade-package
ruff` (or the relevant package). Review the lock diff and run the usual checks;
unrelated versions should stay pinned. Use `uv lock --directory ci --check`
to verify manifest/lock consistency. Do not run `uv sync` from the repository
root: the root project and root `uv.lock` retain integration release metadata.

For local installation, export both groups with the flags from
[Validate](.github/workflows/validate.yml), choose a temporary output directory,
and use the same hash-checking pip commands in a Python virtual environment.

Both workflows require Python **3.14.10 or a later 3.14 patch** and check for
the latest available patch, including when an older runner cache exists. The
dependency inputs require at least **pip 26.2.2** and **certifi 2026.10.19**.
The current environment and lockfile tooling require **uv 0.13.4**
or newer following the
[Python security guidance for the eMudhra incident](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576).
The HA 2026.11.0 environment requires uv 0.13.6 and the CI project constrains
multidict to 6.9.1 or newer. Use the pinned, hash-checked pip install commands from
[Validate](.github/workflows/validate.yml) in a virtual environment.
Run `python -m pip check` and the installed security-baseline check before
tests. Compatibility jobs enforce `UV_OFFLINE=true` throughout; sockets are
allowed only to the local test server. The separate advisory job queries fixed
PyPI HTTPS metadata for all 149 registry package/version pairs, including both
fixtures and all platforms. Any active advisory or unknown result fails Quality.
See [the full baseline](docs/CI_SECURITY_BASELINE.md) for scope and review steps.

```shell
UV_OFFLINE=true python -m pytest -q --disable-socket --allow-hosts=127.0.0.1,::1 \
  --cov=custom_components/meiertobler_smartguard \
  --cov-report=term-missing --cov-report=json:coverage.json --cov-fail-under=100
python scripts/check_quality_coverage.py
```

Configuration forms use Home Assistant's probatio schema types. Keep the saved
host suggestion covered when updating the test baseline.

## Release candidates

Release metadata must use the same stable version in `manifest.json` and
`pyproject.toml`. A release candidate is created only from an annotated
`vMAJOR.MINOR.PATCH` tag whose commit is part of `main`.

Pushing such a tag runs the read-only Release Gate. It repeats all repository,
typing, and test checks and uploads a deterministic integration ZIP plus its
SHA-256 checksum as a temporary workflow artifact. It does not create or
publish a GitHub release. Publication remains a separate manual review step.

Release artifacts may only be written inside the repository's `dist` directory.
Relative `--output-directory` paths are interpreted from the repository root,
regardless of the working directory. Paths and directory symlinks that escape
`dist` are rejected before any output is created. Existing artifact symlinks
are replaced without writing to their targets.
