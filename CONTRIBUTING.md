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
package, pinned with Home Assistant to the advertised minimum of **2026.11.0**.
The protected **Quality** check requires the complete integration and blueprint
test suite. Keep the HA and fixture versions aligned with `hacs.json`. If the
development target later moves ahead of the advertised minimum, test both
supported baselines in separate environments.

`.github/requirements-ci.txt` is compiled from `requirements-ci.in` by uv. Its
header records `--universal` and the Python version used for resolution.
Dependabot uses the `uv` ecosystem for `/.github`, which preserves these
options. Keep this updater and the universal header so tool updates retain
the macOS/Windows dependencies and environment markers. Retain
`--generate-hashes` as well: CI rejects packages without their recorded SHA-256
hashes. Existing dependency versions must remain unchanged when adding hashes.

Both CI workflows install wheels by default. The source-build exception is
`pyric`, whose pinned version provides a source archive. It must match the
hashes in the requirements file. Builds use `--no-build-isolation` and `--no-deps`, so
pip does not automatically fetch additional build tools or dependencies.
`requirements-build.txt`, compiled from `requirements-build.in`, pins and hashes
the build tools installed first. `pip check` verifies the final dependency set.
Review the source-build exception whenever the pyric pin changes.

For a manual Ruff update, use the command recorded in the requirements header
with `--upgrade-package ruff==<new-version>` added. Review the dependency diff
and run the usual checks; unrelated versions should stay pinned.

Both workflows require Python **3.14.10 or a later 3.14 patch** and check for
the latest available patch, including when an older runner cache exists. The
dependency inputs require at least **pip 26.2.2** and **certifi 2026.10.19**.
The current environment and the external lockfile compiler require **uv 0.13.4**
or newer following the
[Python security guidance for the eMudhra incident](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576).
The HA 2026.11.0 environment requires uv 0.13.6 and the lock input requires
multidict 6.9.1 or newer. Use the pinned, hash-checked pip install commands from
[Validate](.github/workflows/validate.yml) in a virtual environment.
Run `python -m pip check` before the tests. The suite allows socket connections
only to the local test server.

```shell
python -m pytest -q --disable-socket --allow-hosts=127.0.0.1,::1 \
  --cov=custom_components/meiertobler_smartguard \
  --cov-report=term-missing --cov-fail-under=95
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
