# @releaseway/npm-actions-fixture

Permanent integration fixture for releaseway/npm-actions.

This package exists only to exercise real npm registry publication behavior, including Trusted Publishing OIDC, exact-version reconciliation, staged publishing, and later native distribution scenarios.

It is not intended for application dependencies or production use.

Published versions use prerelease identifiers and the npm `fixture` dist-tag so they do not participate in a normal `latest` release line.
