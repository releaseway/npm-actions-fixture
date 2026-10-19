#!/usr/bin/env bash
set -euo pipefail

case "${COMMAND_ALIASES:-false}" in
  true|false) ;;
  *) echo 'command-aliases must be true or false' >&2; exit 1 ;;
esac

consumer="$RUNNER_TEMP/native-consumer"
mkdir -p "$consumer"
printf '%s\n' '{"private":true}' >"$consumer/package.json"
pnpm --dir "$consumer" add --ignore-scripts \
  --registry=https://registry.npmjs.org/ \
  "@releaseway/npm-actions-fixture@$FIXTURE_VERSION"

if [ -n "${EXPECTED_INTEGRITY:-}" ]; then
  node scripts/verify-installed-integrity.mjs "$consumer/pnpm-lock.yaml" "$FIXTURE_VERSION" "$EXPECTED_INTEGRITY"
fi

commands=(npm-actions-native-fixture)
if [ "${COMMAND_ALIASES:-false}" = true ]; then commands+=(rw-npm-fixture); fi
for command in "${commands[@]}"; do
  test "$("$consumer/node_modules/.bin/$command" --probe)" = npm-actions-native-fixture-ok
done
cache_root="$XDG_CACHE_HOME/releaseway/npm-actions/native/v2/sha256"
test -d "$cache_root"
test "$(find "$cache_root" -type f -name archive.bin | wc -l)" -eq 1
test "$(find "$cache_root" -type f -name metadata.json | wc -l)" -eq 1
find "$cache_root" -type f -printf '%P %s %T@\n' | LC_ALL=C sort >"$RUNNER_TEMP/cache-before.txt"
chmod -R a-w "$cache_root"
for command in "${commands[@]}"; do
  test "$("$consumer/node_modules/.bin/$command" --probe)" = npm-actions-native-fixture-ok
done
find "$cache_root" -type f -printf '%P %s %T@\n' | LC_ALL=C sort >"$RUNNER_TEMP/cache-after.txt"
diff -u "$RUNNER_TEMP/cache-before.txt" "$RUNNER_TEMP/cache-after.txt"
