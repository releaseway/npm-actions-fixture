# @releaseway/npm-actions-fixture

Permanent integration fixture for releaseway/npm-actions.

This package exists only to exercise real npm registry publication behavior, including Trusted Publishing OIDC, exact-version reconciliation, staged publishing, and later native distribution scenarios.

It is not intended for application dependencies or production use.

Automated fixture versions use prerelease identifiers and the npm `fixture` dist-tag. The one-time bootstrap publication created `0.0.1-fixture.0`; all subsequent publication is performed by `publish.yml` through npm Trusted Publishing OIDC.

## Trusted Publishing

The package identity is already bootstrapped. Configure npm Trusted Publishing for:

- GitHub organization: `releaseway`
- Repository: `npm-actions-fixture`
- Workflow filename: `publish.yml`
- Allowed actions: direct publish and staged publish

The bootstrap credential is no longer part of the fixture flow. Revoke the npm bootstrap token and delete the `NPM_BOOTSTRAP_TOKEN` repository secret after Trusted Publishing is configured.
