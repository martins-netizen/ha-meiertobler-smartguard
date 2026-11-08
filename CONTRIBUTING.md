# Contributing

The project is public and uses controlled development after its first release.
Changes use a feature, fix, or documentation branch and a pull request into
`main`. The active repository ruleset blocks direct changes to `main` and
requires the Quality, Hassfest, and HACS checks.

Before opening a pull request:

1. run `python3 scripts/validate.py`;
2. run Ruff, MyPy, and both complete test suites as documented in the
   [development checks](docs/TECHNICAL_REFERENCE.md#development-checks);
3. verify that no private installation data are present;
4. describe any security impact in the pull-request template.

Do not include credentials, internal network details, real device identifiers,
or exported diagnostics. Use synthetic identifiers and addresses from the
documentation ranges such as `192.0.2.0/24`.

Dependency updates are reviewed through normal pull requests. They are never
merged automatically.

## CI dependency updates

The current test environment uses the official
[`pytest-homeassistant`](https://github.com/home-assistant/core/tree/2026.11.0/packages/pytest-homeassistant)
package, pinned to Home Assistant 2026.11.0. The retired
`pytest-homeassistant-custom-component` package is used only for the frozen
2026.9.0 compatibility environment. Never install the two plugins together.
`tests/ha_helpers.py` provides shared helper imports; both environments run the
complete integration and blueprint test suite with the same coverage threshold.
The protected **Quality** check succeeds only when both environments succeed.

| Environment | Home Assistant | Requirements | Pytest plugin |
| --- | --- | --- | --- |
| Current HA | 2026.11.0 | `.github/requirements-ci.txt` | `pytest-homeassistant` |
| Minimum HA | 2026.9.0 | `.github/requirements-ci-minimum.txt` | `pytest-homeassistant-custom-component` |

This matrix describes development CI on `main`. Historical release notes retain
the environment used for their tagged source; changing CI does not publish a
new integration version.

`.github/requirements-ci.txt` is compiled from `requirements-ci.in` by uv.
`requirements-ci-minimum.txt` is compiled separately from
`requirements-ci-minimum.in`; its HA and fixture versions must stay aligned with
the advertised minimum in `hacs.json`. Keep that baseline fixed during routine
Dependabot updates.
Its header records `--universal` and the Python version used for resolution.
Dependabot uses the `uv` ecosystem for `/.github`, which preserves these
options. Keep this updater and the universal header so tool updates retain
the macOS/Windows dependencies and environment markers. Retain
`--generate-hashes` as well: CI rejects packages without their recorded SHA-256
hashes. Existing dependency versions must remain unchanged when adding hashes.

Both CI workflows install wheels by default. The only source-build exceptions
are `mock-open` (minimum-version tests only) and `pyric`, whose pinned
versions provide no wheels. Their source archives must match the hashes in
the selected requirements file. Builds use `--no-build-isolation` and `--no-deps`, so
pip does not automatically fetch additional build tools or dependencies.
`requirements-build.txt`, compiled from `requirements-build.in`, pins and hashes
the build tools installed first. `pip check` verifies the final dependency set.
Review the source-build allowlist whenever these two dependencies change.

For a manual Ruff update, use the command recorded in the requirements header
with `--upgrade-package ruff==<new-version>` added. Review the dependency diff
and run the usual checks; unrelated versions should stay pinned.

Both workflows require Python **3.14.10 or a later 3.14 patch** and check for
the latest available patch, including when an older runner cache exists. The
dependency inputs require at least **pip 26.2.2** and **certifi 2026.10.19**.
The current environment and the external lockfile compiler require **uv 0.13.4**
or newer following the
[Python security guidance for the eMudhra incident](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576).
The current HA 2026.11.0 environment requires uv 0.13.6. The isolated HA 2026.9.0
compatibility environment retains HA's original uv 0.12.5 dependency, which is
not invoked as a package installer or by the tests. Only hash-checked pip installs
are used in either environment, and tests allow socket connections only to the
local test server. Do not use the baseline environment for dependency updates.
Keep the runtime, build-tool and test dependency sets consistent; do not bypass
Home Assistant's dependency constraints. These development requirements do not
update Python in an existing Home Assistant installation.

Run the second environment in its own virtual environment using the same build
tools and install flags, replacing `requirements-ci.txt` with
`requirements-ci-minimum.txt`. `python -m pip check` must pass in both. Run tests:

```shell
python -m pytest -q --disable-socket --allow-hosts=127.0.0.1,::1 \
  --cov=custom_components/meiertobler_smartguard \
  --cov-report=term-missing --cov-fail-under=95
```

Current and minimum HA tests must both pass before merging.

Configuration forms use Home Assistant's probatio schema types, available in
the supported Home Assistant 2026.9.0 baseline, to match the newer Home Assistant
type contract. Keep the saved host suggestion covered when updating the test
baseline.

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
