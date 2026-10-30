# Release and publication checklist

This checklist separates technical release validation from publication and
post-release distribution tests. Tagging and passing the Release Gate never
publish automatically; the owner must make a separate publication decision.

## 0.5.0 operating-readings and repairs candidate

Status: prepared release candidate; **not yet published**. See
[0.5.0 release notes](RELEASE_NOTES_0.5.0.md). Existing published tags/assets
remain unchanged; the Release Gate still never publishes automatically.

- [x] Merge eight optional read-only operating entities and configuration repairs.
- [x] Include the tested blueprint ownership guard and guided setup; imported
      blueprints and existing production automations are not automatically replaced.
- [x] Choose 0.5.0 for additive functionality and align manifest/project/root lock.
- [x] Prepare versioned notes, changelog, entity counts and upgrade guidance.
- [x] Complete validation, Ruff, strict MyPy, all tests and deterministic bundle
      inspection on the exact versioned candidate.
- [ ] Review the release PR and merge after Quality, Hassfest, HACS and SonarCloud.
- [ ] Verify those four checks again on the exact final main commit.
- [ ] Create annotated `v0.5.0`, pass its tagged Release Gate and inspect its ZIP.
- [ ] Explicitly publish the full GitHub release with both verified assets.
- [ ] Complete the actual HACS upgrade, restart, old-ID and additional-entity check.

The read-only live inventory verified the eight selected datapoints. It was not
an installation test of 0.5.0. Repair fault injection, a new physical mode cycle
and migration to a newly saved blueprint automation are not claimed or required
as repetitions of already completed unchanged-behavior checks. A clean install
on the minimum supported HA version remains separately unconfirmed.

Local candidate checks passed on Python 3.14.10 / HA 2026.10.4: **209 tests and
26 subtests**, **100% integration statement/branch coverage**. Two independent
ZIP builds were identical; all **19 integration files** matched their source
bytes. This is a candidate build, not the still-pending tagged Release Gate.

## Published 0.4.1 documentation patch record

Status: **published on 2026-10-23 at 05:40:13 UTC**. HACS update, new README/graphic
and all 15 existing entities were user-confirmed on **2026-10-25**. See
[0.4.1 release notes](RELEASE_NOTES_0.4.1.md) for exact scope and source references.

- [x] Prepare the concise README, illustrative graphic and linked guides.
- [x] Keep manifest, project and lock-file root versions at 0.4.1.
- [x] Retain 0.4.0 runtime logic; only its manifest version changes.
- [x] Pass the publication source checks, annotated tag and Release Gate.
- [x] Publish the full GitHub release with both verified assets.
- [x] Confirm the 0.4.1 HACS update, new overview and existing entities.

Current annotated `v0.4.1` source: `094845ea561b3d23ccf26bc9fea0913de68a5b5d`.
Its [subsequent tagged revalidation](https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/runs/40373063287)
passed after repository metadata maintenance. ZIP SHA-256
`bbc4734035a05897faa24063822a3da9a06d7a7e346abdb155e10121e4ffba22`;
original assets and tag remain unchanged by this release preparation.
The HACS/UI confirmation is not a new independent byte audit.

## Published 0.4.0 record

Status: published on 2026-10-22 at 20:01:41 UTC. The maintainer confirmed the
HACS upgrade and entity availability on 2026-10-23; see
[HACS_TEST_V0.4.0.md](HACS_TEST_V0.4.0.md) for scope and limitations.

- [x] Select 0.4.0 for the additive storage measurements and release/CI hardening.
- [x] Keep manifest, project and root lock-file versions consistent.
- [x] Prepare [0.4.0 release notes](RELEASE_NOTES_0.4.0.md) and changelog.
- [x] Complete the merged feature's Home Assistant installation test; see
      [Additional measurements](ADDITIONAL_MEASUREMENTS.md).
- [x] Pass release PR #24 and final source `main` checks: Quality, Hassfest,
      HACS and SonarCloud. Source: `02b7cff7869a642b2191d3877e19f211cc72a35f`.
- [x] Create the annotated `v0.4.0` tag and pass its
      [Release Gate](https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/runs/39843987656).
- [x] Inspect and verify the tagged ZIP/checksum and all 18 integration files.
      SHA-256: `9b856d6c16bb023262992da7a9528a71cdc231ce92abe7e4e54daea3182bb4b2`.
- [x] Explicitly approve and publish the
      [full latest release](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/tag/v0.4.0).
- [x] Verify the public release, latest status and both downloaded assets.
- [x] Receive user confirmation of the HACS update to published 0.4.0 and all
      existing entities present. The prior installation was 0.3.0 plus the
      already-tested storage feature; no new independent byte check is claimed.

Security PR #23, release PR #24 and README PR #25 were merged before tagging.
The publication check did not contact Home Assistant. The completed feature
installation and the subsequent user-confirmed HACS upgrade are distinct records.

The completed feature test need not be repeated solely for a manifest version
change. Preserve that evidence and verify that the release's runtime files are
otherwise identical. Initial installation on the minimum supported Home
Assistant version remains a distinct, unclaimed check. Existing guarded night
switching has been exercised in the field; read-only measurements do not
require another physical mode change.

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
- [x] HACS default-catalogue submission opened on 2026-09-22:
      [hacs/default#11172](https://github.com/hacs/default/pull/11172).
- [x] HACS maintainers approved and merged the default-catalogue submission
      on 2026-10-19 in
      [hacs/default#11172](https://github.com/hacs/default/pull/11172).

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
- [ ] Run Ruff, strict MyPy, and the complete test suite in the
      [technical reference](TECHNICAL_REFERENCE.md).
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
- [ ] Complete the relevant Home Assistant smoke checks for the selected
      candidate: setup, polling, new entities, reload and recovery.

Retain existing evidence for unchanged mode-write/readback and removal behavior.
Adding read-only values does not require a new physical mode-switch cycle.

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

## 6. HACS default-repository submission

Submitted on 2026-09-22 for `v0.3.0` in
[hacs/default#11172](https://github.com/hacs/default/pull/11172). HACS maintainers
approved and merged the submission on 2026-10-19.

- [x] Verify that the repository is public and hosted on GitHub.
- [x] Verify that the official HACS action and Hassfest pass without errors or
      ignores.
- [x] Verify that at least one full GitHub release exists.
- [x] Verify that repository description, topics, issues, brand assets,
      `manifest.json`, and `hacs.json` meet current HACS requirements.
- [x] Submit the repository only from the owner or a major contributor and
      follow the current HACS submission template.
- [x] HACS maintainers approve and merge the default-catalogue submission.

The repository is included in the default HACS catalogue. Distribution of the
updated catalogue to users can take up to eight hours after approval. Existing
HACS installations do not need to be reinstalled because of the catalogue
addition. The completed custom-repository installation test is recorded in
[HACS_TEST_V0.3.0.md](HACS_TEST_V0.3.0.md).

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
