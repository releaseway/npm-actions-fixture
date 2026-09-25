# @releaseway/npm-actions-fixture

Permanent integration fixture for releaseway/npm-actions.

This package exists only to exercise real npm registry and GitHub Release behavior, including Trusted Publishing OIDC, exact-version reconciliation, staged publishing, and native distribution.

It is not intended for application dependencies or production use.

The committed package remains an ordinary non-native fixture. Workflows may rewrite checkout-local metadata for an individual scenario before invoking npm-actions.

## Trusted Publishing

The package identity is already bootstrapped. Configure npm Trusted Publishing for the staged workflow:

- GitHub organization: `releaseway`
- Repository: `npm-actions-fixture`
- Workflow filename: `publish.yml`
- Allowed action: staged publish

The bootstrap credential is no longer part of the fixture flow.

## Staged fixture

`publish.yml` keeps the committed Releaseway policy at its staged default and exercises the real npm staged-publishing path.

## Direct native fixture

`direct.yml` reuses the existing direct Trusted Publisher connection and extends that scenario to the real native runtime path. Configure npm Trusted Publishing for:

- GitHub organization: `releaseway`
- Repository: `npm-actions-fixture`
- Workflow filename: `direct.yml`
- Allowed action: enable `Allow npm publish`

Repository release immutability must also be enabled before dispatching this workflow. The native workflow creates a draft Release, attaches the fixture asset, publishes the Release, and waits until GitHub reports that the Release is immutable and the asset has a SHA-256 digest.

The workflow-local package version defaults to `0.0.6-native.0` and may be advanced with the `fixture-version` input. The committed `package.json` version is not changed by the workflow.

For a new native fixture version, `direct.yml` performs:

1. rewrite checkout-local package metadata to add the native bin and requested fixture version;
2. rewrite checkout-local Releaseway policy to direct mode with a Linux x64 GitHub Release distribution;
3. create or reuse the same-commit `native-v<version>` immutable Release;
4. run npm-actions through Trusted Publishing OIDC;
5. wait for the exact version and SHA-512 artifact to become live;
6. install that exact package version from npm using `--ignore-scripts`;
7. execute the installed native command once to populate the v2 runtime cache;
8. make the cache read-only and execute the command again;
9. verify that the cache file snapshot did not change on the second invocation.

The fixture asset itself is `native/fixture.sh`, packed into `npm-actions-native-fixture_linux_x64.tar.gz` with the executable path `bin/npm-actions-native-fixture`. It prints `npm-actions-native-fixture-ok` only for the expected `--probe` invocation.

Rerunning `direct.yml` with the same version and commit and `expected-state=existing` exercises exact-artifact reconciliation without another npm mutation. A native fixture version is intentionally not reusable from a different source commit because npm-actions requires the immutable Release tag to resolve to the current `GITHUB_SHA`.

Cross-platform installed-wrapper behavior is covered in the npm-actions repository by the hosted runtime/install matrix on Linux x64/arm64, macOS x64/arm64, and Windows x64/arm64. The real registry native fixture is intentionally Linux x64 so it can focus on GitHub Release provenance, npm OIDC publication, public installation, first-run download, and cache reuse.
