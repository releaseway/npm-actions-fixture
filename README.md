# @releaseway/npm-actions-fixture

Permanent integration fixture for releaseway/npm-actions. Development and consumer
installation checks use the pnpm version pinned in `package.json`. Install verifier
dependencies with `corepack pnpm install --frozen-lockfile`.

This package exercises real npm registry and GitHub Release behavior: registry-first
version selection, Trusted Publishing OIDC, staged submissions, and native installation
and execution. It is not intended for application dependencies or production use.

The committed package remains an ordinary non-native fixture. Fixture-specific native
bin metadata and the legacy package-json version scenario are prepared locally;
tag-derived scenarios preserve the source version. Publication channels are declared as
stable `latest` and prerelease `next` in Releaseway policy, without rewriting
`publishConfig.tag`.

Both workflows accept a full `action-ref` SHA, verify the checked-out SHA and run
`./npm-action`. Read each workflow's dispatch defaults at the tested fixture commit for
its selected automation SHA and historical version.

## Result contract

`already-published` means the exact version was public at initial lookup. The action
skips packaging and native Release validation for that version and makes no claim that
current source equals the historical artifact.

`published` means a prepared candidate is live with the expected SHA-512, including an
identical concurrent publication. `staged` means npm accepted a stage submission; the
version is not yet confirmed public.

The caller selects a new version when new fixture source or a new action runtime needs
to be published. Both workflows assert the returned package name, version, and expected
state.

## Trusted Publishing

Both existing workflows also accept an optional `prepacked-version` in the form
`0.0.N-prepacked.M`. This adds an ordinary-package build/consumer-verification job
and a separate publisher job using the same package and Trusted Publisher workflow
identity. Existing native direct and ordinary staged acceptance jobs remain intact.
Use distinct fresh prepacked versions for direct and stage runs.

The build job seals one tarball and its source/SHA-512 manifest into a bundle. The
publish job downloads its exact artifact ID, checks wrong-SRI rejection before
publication, then publishes that archive. Direct acceptance also deletes the
local tarball and checks a verified already-public retry. The separate
`prepacked-acceptance-<attempt>` artifact contains its receipt, source manifest and
verification reports. Existing `releaseway-acceptance-<attempt>` receipts keep
their original schemas and meanings. Stage acceptance never approves a version.

The package identity is already bootstrapped. Configure npm Trusted Publishing for the staged workflow:

- GitHub organization: `releaseway`
- Repository: `npm-actions-fixture`
- Workflow filename: `publish.yml`
- Allowed action: staged publish

The bootstrap credential is no longer part of the fixture flow.

## Staged fixture

For the complete preparation/publication flow, dispatch `publish.yml` with
`prepare-release=true`, `version-source=git-tag`, `expected-state=staged`, and the
planned `fixture-version` from the planner result.

The committed release and
npm policies select `prepared-npm-v` tags and `next`. Releaseway plans the version,
the fixture checks that expectation, then Releaseway resumes the saved plan and
atomically pushes the marker commit and tag. npm-actions receives the prepared
commit through its JavaScript action input and packs its tag-derived version.
This path does not run the metadata preparation script or rewrite `package.json`.

Evidence retains the workflow source SHA and separately records the prepared SHA.

`publish.yml` keeps the committed Releaseway policy at its staged default. It accepts
`fixture-version` in the form `0.0.N-fixture.M` and `expected-state` as either `staged`
or `already-published`.

The workflow defaults use a historical version with `already-published` to exercise
version lookup without a new submission. To exercise actual staged publication, choose a
fresh fixture version and `expected-state=staged`. Approval remains a maintainer
operation. A pending staged version is not an already-public version, and a conflicting
submission is expected to fail.

## Direct native fixture

`direct.yml` uses the direct Trusted Publisher connection. Configure npm Trusted Publishing for:

- GitHub organization: `releaseway`
- Repository: `npm-actions-fixture`
- Workflow filename: `direct.yml`
- Allowed action: enable `Allow npm publish`

The defaults select a historical native version with `command-aliases=true` and
`expected-state=already-published`. For this scenario the workflow skips Release
creation and source-commit comparison, invokes npm-actions to verify the version is
already public, then installs and executes the published CLI. It may run from a later
source commit than the original Release. It does not republish the historical package or
test a newly generated runtime.

To publish a new native fixture, select a fresh `0.0.N-native.M` version and
`expected-state=published`. Repository release immutability must be enabled. Product
steps build the deterministic Linux x64 asset. `releaseway/actions/prepare` binds the
same-commit `native-v<version>` tag and `releaseway/actions` publishes or resumes its
immutable prerelease with verified asset digests, before npm-actions publishes to `next`.

The action prepares only an unpublished candidate and confirms its exact SHA-512 in the live registry.

Both native scenarios install the exact version with `--ignore-scripts` on Node 22, 24
and 26, each with a separate empty native cache. They execute the CLI, make its
populated cache read-only, execute again and compare file snapshots. Fresh `published`
runs also compare installed package-lock SHA-512 with the action report's frozen plan.
Historical lookup remains a separate result.

The fixture asset is `native/fixture.sh`, packed into
`npm-actions-native-fixture_linux_x64.tar.gz` at `bin/npm-actions-native-fixture`. It
prints `npm-actions-native-fixture-ok` for the expected `--probe` invocation.

Cross-platform installed-wrapper behavior is covered in the npm-actions repository by
the runtime/install matrix on Linux x64/arm64, macOS x64/arm64, and Windows x64/arm64.
This real-registry native fixture targets Linux x64 to exercise GitHub Release
provenance, npm OIDC publication, installation, first-run download, and cache reuse.

## Native command aliases

For an alias-capable candidate, dispatch `direct.yml` with its full `action-ref`,
a fresh native version, `expected-state=published`, and `command-aliases=true`.
Preparation maps both `npm-actions-native-fixture` and `rw-npm-fixture` to the same
generated launcher. Every Node 22/24/26 consumer executes both names, then repeats
them against one read-only cache. Successful evidence records the alias names.

The alias option defaults to `true` with the alias-capable native fixture.
Set it to `false` for an older published fixture without aliases. Staged non-native
fixtures do not use this
option. A historical lookup still cannot certify new candidate packaging.

## Candidate acceptance

Supply the candidate's full 40-character `action-ref`, a fresh version and fresh
expected state (`staged` or `published`). New candidates must implement `report-path`.
Stable defaults continue to exercise historical lookup.

Both workflows accept `version-source=package-json` (default) or `git-tag`. For manual
tags without `prepare-release`,
create `npm-fixture-v<fixture-version>` targeting the fixture workflow commit before
dispatch. Use one matching version tag per fixture commit; ordinary and native
tag-derived versions need separate commits.

Both prerelease scenarios publish to `next`. With `prepare-release=true`, staged
publication instead uses the planner-created `prepared-npm-v` tag described above.

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

## App-free rc/stable acceptance

Keep the registered caller `direct.yml`. Its new `app-free` input defaults to false,
so the existing native acceptance remains unchanged.

With `app-free=true`, supply
both full candidate SHAs: `actions-ref` for version/tag/Release operations and the
existing `action-ref` for npm-actions. The workflow creates rc and stable tags on
the same clean source before preparing fixture-only package metadata, then selects
each tag explicitly for npm publication. Both native packages are installed with
scripts disabled and executed on Node 22, 24 and 26; lockfile integrity is compared
with the candidate's frozen plan.

The namespace is `app-free-v`, initial version is `0.0.100`, and npm channels are
`app-free-rc` / `app-free-stable`. Existing fixture channels and workflows are
preserved. Normal source-tag history calculates subsequent versions. No new GitHub
App, PAT or npm publish token is required; the caller's existing Trusted Publisher
must allow direct publication.

Already-public versions do not prove fresh candidate
packaging and therefore cannot satisfy this readiness artifact. A dedicated rerun
using explicit `rc-tag` and `stable-tag` can reconcile remote results, but its skip
results do not replace the original fresh-publication evidence.

Evidence artifact: `app-free-acceptance-<run_attempt>`. The combined read-only checker
in actions/scripts/verify-app-free-evidence.py also requires current legacy notes,
stage and native runs, exact candidate push CI, and the release fixture's complete
tap/Pages evidence. It rejects stale attempts, missing matrix entries and substituted
source/candidate identities. Nothing in the local tests marks live readiness passed.
