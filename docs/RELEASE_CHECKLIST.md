# Release and publication checklist

This checklist separates technical release validation from publication and
post-release distribution tests. Tagging and passing the Release Gate never
publish automatically; the owner must make a separate publication decision.

## Published 0.3.0 record

- [x] Protected source commit:
      `94b7305c3fcb61b3647452637fb479735a66e8b7`.
- [x] Annotated tag: `v0.3.0`.
- [x] Release Gate run: `35496534407`.
- [x] Deterministic ZIP SHA-256:
      `190b3aeb71e43fed8592242416ed5cd702bdbc9c2e82bdb279b4cea4d9209dc5`.
- [x] Field smoke test passed on 2026-09-20.
- [x] Public Quality, Hassfest, and official HACS validation passed.
- [x] Public release reviewed and published on 2026-09-21.
- [x] `main` remains protected by the active `Protect main` ruleset.
- [x] HACS custom-repository download, restart, and reload test passed on
      2026-09-21. See [HACS_TEST_V0.3.0.md](HACS_TEST_V0.3.0.md).

## 1. Prepare a version pull request

- [ ] Choose one stable version in `MAJOR.MINOR.PATCH` form.
- [ ] Update the version in
      `custom_components/meiertobler_smartguard/manifest.json` and
      `pyproject.toml`, and the root package entry in `uv.lock` in the same pull
      request.
- [ ] Add the version to `CHANGELOG.md` and prepare version-specific release
      notes without claiming that the candidate has already been published.
- [ ] Update version-specific documentation and compatibility statements.
- [ ] Confirm that no credentials, internal addresses, serial numbers, device
      identifiers, or unreviewed diagnostics are present.
- [ ] Run `python3 scripts/validate.py`.
- [ ] Run `python3 scripts/release.py check`.
- [ ] Run Ruff, strict MyPy, and the complete test suite documented in the
      README.
- [ ] Open a pull request and require successful Quality, Hassfest, and HACS
      checks before review.

## 2. Approve the exact source commit

- [ ] Review the complete pull-request diff and its security impact.
- [ ] Squash-merge only while all required checks are successful.
- [ ] Update local `main` with a fast-forward-only pull.
- [ ] Record the exact full commit SHA selected for the release.
- [ ] Confirm that the final Validate workflow for that exact `main` commit is
      successful.
- [ ] Confirm that the working tree is clean.

Do not tag a feature branch, an unreviewed commit, or a commit that is not part
of `main`.

## 3. Run the read-only release gate

- [ ] Create an annotated tag named `vMAJOR.MINOR.PATCH` on the approved full
      commit SHA.
- [ ] Verify the local tag object and target before pushing it.
- [ ] Push only that tag.
- [ ] Wait for the **Release Gate** workflow on the tag to succeed.
- [ ] Download the temporary ZIP and `.sha256` workflow artifacts.
- [ ] Recalculate SHA-256 locally and compare it with the supplied checksum.
- [ ] Inspect the ZIP file list and confirm that it contains only the expected
      integration files.
- [ ] Install the candidate ZIP in a test Home Assistant instance and complete
      a smoke test of setup, polling, mode write/readback, reload, and removal.

The tag workflow has read-only repository permissions. It validates and builds
artifacts but does not create a GitHub release.

## 4. Publication decision

For a first public release, stop here unless publication is explicitly
approved. Before making a private repository public:

- [ ] Confirm the repository description, topics, license, support status, and
      issues configuration.
- [ ] Enable GitHub Private Vulnerability Reporting when it is available for the
      public repository.
- [ ] Re-read the security policy and known unauthenticated HTTP limitation.
- [ ] Confirm that the repository history contains no private installation data.
- [ ] Make the repository public only as a separate, deliberate action.
- [ ] Run the official HACS action and Hassfest successfully on the public
      repository.
- [ ] Publish the tested SmartGuard blueprint at a stable public URL, verify
      import into a test Home Assistant instance, and add the public link to the
      automation documentation.
- [ ] Mark the Home Assistant `docs-examples` quality rule complete only after
      that public blueprint link and import test exist.

## 5. Create the full GitHub release manually

- [ ] Confirm again that the release tag targets the approved `main` commit.
- [ ] Create a full GitHub release for the existing tag; a tag without a release
      is not sufficient for HACS publication.
- [ ] Attach the inspected deterministic ZIP and its checksum.
- [ ] Write release notes with supported Home Assistant versions, supported
      SmartGuard device type, changes, known limitations, and upgrade steps.
- [ ] Review the draft release and attached checksums before selecting
      **Publish release**.
- [ ] Test installation and update through HACS as a custom repository.

## 6. Optional HACS default-repository submission

- [ ] Verify that the repository is public and hosted on GitHub.
- [ ] Verify that the official HACS action and Hassfest pass without errors or
      ignores.
- [ ] Verify that at least one full GitHub release exists.
- [ ] Verify that repository description, topics, issues, brand assets,
      `manifest.json`, and `hacs.json` meet current HACS requirements.
- [ ] Submit the repository only from the owner or a major contributor and
      follow the current HACS submission template.

Default HACS inclusion is a later, independent decision. Public custom-repository
testing should succeed before submitting it.

## 7. Post-release verification and recovery

- [x] Confirmed that HACS resolves the published version and installs the
      expected tagged `custom_components` source tree. The attached release
      ZIP was separately verified; `hacs.json` does not enable `zip_release`.
- [ ] Confirm a clean installation and restart on the minimum supported Home
      Assistant version.
- [ ] Monitor issues without requesting private diagnostics in public.
- [ ] If a release is unsafe, document the impact, remove the affected release
      asset or mark the release accordingly, and publish a corrected version.
- [ ] Do not move or silently replace an existing version tag or asset.
