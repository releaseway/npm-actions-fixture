#!/usr/bin/env bash
set -euo pipefail
for version in "$RC_VERSION" "$STABLE_VERSION"; do
  consumer="$(mktemp -d "$RUNNER_TEMP/app-free-consumer-XXXXXX")"
  printf '%s\n' '{"private":true}' > "$consumer/package.json"
  npm install --prefix "$consumer" --ignore-scripts --registry=https://registry.npmjs.org/ "@releaseway/npm-actions-fixture@$version"
  test "$(node -e 'console.log(JSON.parse(require("node:fs").readFileSync(process.argv[1], "utf8")).version)' "$consumer/node_modules/@releaseway/npm-actions-fixture/package.json")" = "$version"
  test "$("$consumer/node_modules/.bin/npm-actions-native-fixture" --version)" = "$version"
  test "$("$consumer/node_modules/.bin/npm-actions-native-fixture" --probe)" = npm-actions-native-fixture-ok
  if [ "$version" = "$RC_VERSION" ]; then report="$RC_REPORT"; else report="$STABLE_REPORT"; fi
  node --input-type=module - "$consumer/package-lock.json" "$report" <<'JS'
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const [lock, report] = process.argv.slice(2).map(path => JSON.parse(readFileSync(path, 'utf8')));
assert.equal(lock.packages['node_modules/@releaseway/npm-actions-fixture'].integrity, report.plan[0].integrity);
JS
  rm -rf "$consumer"
done
