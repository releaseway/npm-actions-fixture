# @releaseway/npm-actions-fixture

Permanent integration fixture for releaseway/npm-actions.

This package exercises real npm registry and GitHub Release behavior: registry-first version selection, Trusted Publishing OIDC, staged submissions, and native installation and execution. It is not intended for application dependencies or production use.

The committed package remains an ordinary non-native fixture. Each workflow rewrites checkout-local metadata for its requested scenario; it does not commit version changes. Both workflows pin the same reviewed npm-actions commit.

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

The inputs default to `fixture-version=0.0.6-native.0` and `expected-state=already-published`. For this scenario the workflow skips Release creation and source-commit comparison, invokes npm-actions to verify the version is already public, then installs and executes the published CLI. It may run from a later source commit than the original Release. It does not republish the historical package or test a newly generated runtime.

To publish a new native fixture, select a fresh `0.0.N-native.M` version and `expected-state=published`. Repository release immutability must be enabled. The workflow creates or reuses a same-commit `native-v<version>` Release, uploads the Linux x64 asset, and waits for immutability and a SHA-256 asset digest before invoking npm-actions. The action prepares only an unpublished candidate and confirms its exact SHA-512 in the live registry.

For both native scenarios, installation uses the exact requested npm version and `--ignore-scripts`. The workflow starts with an empty native cache, executes the installed command, makes the populated cache read-only, executes again, and compares cache file snapshots. The second run checks reuse without file changes; it does not independently assert that all network access was blocked.

The fixture asset is `native/fixture.sh`, packed into `npm-actions-native-fixture_linux_x64.tar.gz` at `bin/npm-actions-native-fixture`. It prints `npm-actions-native-fixture-ok` for the expected `--probe` invocation.

Cross-platform installed-wrapper behavior is covered in the npm-actions repository by the runtime/install matrix on Linux x64/arm64, macOS x64/arm64, and Windows x64/arm64. This real-registry native fixture targets Linux x64 to exercise GitHub Release provenance, npm OIDC publication, installation, first-run download, and cache reuse.
