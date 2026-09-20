# Contributing

The project is in controlled private development before its first public
release. Changes use a feature or fix branch and a pull request into `main`.
Direct changes to `main` are not the normal workflow after branch protection is
enabled.

Before opening a pull request:

1. run `python3 scripts/validate.py`;
2. run Ruff, MyPy, and the test suite as documented in `README.md`;
3. verify that no private installation data are present;
4. describe any security impact in the pull-request template.

Do not include credentials, internal network details, real device identifiers,
or exported diagnostics. Use synthetic identifiers and addresses from the
documentation ranges such as `192.0.2.0/24`.

Dependency updates are reviewed through normal pull requests. They are never
merged automatically.

## Release candidates

Release metadata must use the same stable version in `manifest.json` and
`pyproject.toml`. A release candidate is created only from an annotated
`vMAJOR.MINOR.PATCH` tag whose commit is part of `main`.

Pushing such a tag runs the read-only Release Gate. It repeats all repository,
typing, and test checks and uploads a deterministic integration ZIP plus its
SHA-256 checksum as a temporary workflow artifact. It does not create or
publish a GitHub release. Publication remains a separate manual review step.
