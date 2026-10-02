#!/usr/bin/env bash
set -euo pipefail

consumer="$RUNNER_TEMP/native-consumer"
mkdir -p "$consumer"
printf '%s\n' '{"private":true}' >"$consumer/package.json"
npm install --ignore-scripts --no-audit --no-fund \
  --registry=https://registry.npmjs.org/ --prefix "$consumer" \
  "@releaseway/npm-actions-fixture@$FIXTURE_VERSION"

if [ -n "${EXPECTED_INTEGRITY:-}" ]; then
  actual="$(jq -r '.packages["node_modules/@releaseway/npm-actions-fixture"].integrity' "$consumer/package-lock.json")"
  test "$actual" = "$EXPECTED_INTEGRITY" || { echo 'installed integrity differs from the candidate plan' >&2; exit 1; }
fi

bin="$consumer/node_modules/.bin/npm-actions-native-fixture"
test "$("$bin" --probe)" = npm-actions-native-fixture-ok
cache_root="$XDG_CACHE_HOME/releaseway/npm-actions/native/v2/sha256"
test -d "$cache_root"
test "$(find "$cache_root" -type f -name archive.bin | wc -l)" -eq 1
test "$(find "$cache_root" -type f -name metadata.json | wc -l)" -eq 1
find "$cache_root" -type f -printf '%P %s %T@\n' | LC_ALL=C sort >"$RUNNER_TEMP/cache-before.txt"
chmod -R a-w "$cache_root"
test "$("$bin" --probe)" = npm-actions-native-fixture-ok
find "$cache_root" -type f -printf '%P %s %T@\n' | LC_ALL=C sort >"$RUNNER_TEMP/cache-after.txt"
diff -u "$RUNNER_TEMP/cache-before.txt" "$RUNNER_TEMP/cache-after.txt"
