# @releaseway/npm-actions-fixture

Permanent integration fixture for releaseway/npm-actions.

This package exists only to exercise real npm registry publication behavior, including Trusted Publishing OIDC, exact-version reconciliation, staged publishing, and later native distribution scenarios.

It is not intended for application dependencies or production use.

Published versions use prerelease identifiers and the npm `fixture` dist-tag so they do not participate in a normal `latest` release line.

## Bootstrap

The first package version is published by the one-time `Bootstrap npm fixture` workflow using a short-lived granular npm token stored as `NPM_BOOTSTRAP_TOKEN`.

After the package exists, configure npm Trusted Publishing for:

- GitHub organization: `releaseway`
- Repository: `npm-actions-fixture`
- Workflow filename: `publish.yml`
- Allowed actions: direct publish and staged publish

The bootstrap token is not used by `publish.yml` and should be revoked after Trusted Publishing is configured.
