#!/usr/bin/env bash
set -euo pipefail

consumer="${1:?consumer directory required}"
deadline=$((SECONDS + 360))
log="$consumer/install.log"
while :; do
  if pnpm --dir "$consumer" add --ignore-scripts \
      --registry=https://registry.npmjs.org/ \
      "@releaseway/npm-actions-fixture@${FIXTURE_VERSION:?fixture version required}" >"$log" 2>&1; then
    cat "$log"
    exit 0
  else
    status=$?
  fi
  cat "$log" >&2
  # npm's compact install metadata can lag the public full-metadata endpoint.
  # Retry only this read/install observation; never resubmit a publication.
  if ((SECONDS >= deadline)) || ! grep -q 'ERR_PNPM_NO_MATCHING_VERSION' "$log"; then
    exit "$status"
  fi
  sleep 5
done
