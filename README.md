# @releaseway/npm-actions-fixture

Permanent integration fixture for releaseway/npm-actions.

This package exercises real npm registry and GitHub Release behavior: registry-first version selection, Trusted Publishing OIDC, staged submissions, and native installation and execution. It is not intended for application dependencies or production use.

The committed package remains an ordinary non-native fixture. Fixture-specific native bin metadata and the legacy package-json version scenario are prepared locally; tag-derived scenarios preserve the source version. Publication channels are declared as stable `latest` and prerelease `next` in Releaseway policy, without rewriting `publishConfig.tag`. Both workflows accept a full `action-ref` SHA, verify the checked-out SHA and run `./npm-action`.

## Result contract

`already-published` means the exact version was public at initial lookup. The action skips packaging and native Release validation for that version and makes no claim that current source equals the historical artifact.

`published` means a prepared candidate is live with the expected SHA-512, including an identical concurrent publication. `staged` means npm accepted a stage submission; the version is not yet confirmed public.

The caller selects a new version when new fixture source or a new action runtime needs to be published. Both workflows assert the returned package name, version, and expected state.

## Trusted Publishing

The package identity is already bootstrapped. Configure npm Trusted Publishing for the staged workflow:

- GitHub organization: `releaseway`
- Repository: `npm-actions-fixture`
- Workflow filename: `publish.yml`
- Allowed action: staged publish

The bootstrap credential is no longer part of the fixture flow.

## Staged fixture

`publish.yml` keeps the committed Releaseway policy at its staged default. It accepts `fixture-version` in the form `0.0.N-fixture.M` and `expected-state` as either `staged` or `already-published`.

The defaults use `0.0.5-fixture.0` with `already-published` to exercise version lookup without a new submission. To exercise actual staged publication, choose a fresh fixture version and `expected-state=staged`. Approval remains a maintainer operation. A pending staged version is not an already-public version, and a conflicting submission is expected to fail.

## Direct native fixture

`direct.yml` uses the direct Trusted Publisher connection. Configure npm Trusted Publishing for:

- GitHub organization: `releaseway`
- Repository: `npm-actions-fixture`
- Workflow filename: `direct.yml`
- Allowed action: enable `Allow npm publish`

The inputs default to `fixture-version=0.0.9-native.0` and `expected-state=already-published`. For this scenario the workflow skips Release creation and source-commit comparison, invokes npm-actions to verify the version is already public, then installs and executes the published CLI. It may run from a later source commit than the original Release. It does not republish the historical package or test a newly generated runtime.

To publish a new native fixture, select a fresh `0.0.N-native.M` version and `expected-state=published`. Repository release immutability must be enabled. Product steps build the deterministic Linux x64 asset. `releaseway/actions/prepare` binds the same-commit `native-v<version>` tag and `releaseway/actions` publishes or resumes its immutable prerelease with verified asset digests, before npm-actions publishes to `next`. The action prepares only an unpublished candidate and confirms its exact SHA-512 in the live registry.

Both native scenarios install the exact version with `--ignore-scripts` on Node 22, 24 and 26, each with a separate empty native cache. They execute the CLI, make its populated cache read-only, execute again and compare file snapshots. Fresh `published` runs also compare installed package-lock SHA-512 with the action report's frozen plan. Historical lookup remains a separate result.

The fixture asset is `native/fixture.sh`, packed into `npm-actions-native-fixture_linux_x64.tar.gz` at `bin/npm-actions-native-fixture`. It prints `npm-actions-native-fixture-ok` for the expected `--probe` invocation.

Cross-platform installed-wrapper behavior is covered in the npm-actions repository by the runtime/install matrix on Linux x64/arm64, macOS x64/arm64, and Windows x64/arm64. This real-registry native fixture targets Linux x64 to exercise GitHub Release provenance, npm OIDC publication, installation, first-run download, and cache reuse.

## Candidate acceptance

Supply the candidate's full 40-character `action-ref`, a fresh version and fresh
expected state (`staged` or `published`). New candidates must implement `report-path`.
Stable defaults continue to exercise historical lookup.

Both workflows accept `version-source=package-json` (default) or `git-tag`. For tags,
create `npm-fixture-v<fixture-version>` targeting the fixture workflow commit before
dispatch. Use one matching version tag per fixture commit; ordinary and native
tag-derived versions need separate commits. Their dist-tags are `fixture` and `native`.

Successful runs upload `releaseway-acceptance-<run_attempt>` with one `acceptance.json`,
retained for 30 days. It records candidate SHA, fixture commit, run/attempt, scenario,
version source, version, state, planned integrity for fresh publication and verified
Node versions for direct consumers. Staged success proves submission; approval and
installation remain separate maintainer actions. Historical lookup cannot certify a
new action release.

Preserve a successful fresh publication run for readiness. If a version was already
submitted or published, choose a fresh version for another candidate test. Direct
publication resolves an identical concurrent publish through matching integrity;
a later rerun that initially sees the version public returns lookup state.

Local contracts: `python3 test/contracts.py`. CI also checks shell syntax/workflows.
Public OIDC acceptance requires the Trusted Publisher connections described above.
